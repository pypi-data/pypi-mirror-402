from datetime import datetime
import pandas as pd
from supabase import create_client, Client
from typing import Union, List, Optional, Dict
from quantmod.markets import getData
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Suppress verbose logging from dependencies
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)



class QuantmodDB:
    """
    QuantmodDB
    ----------------
    Python SDK for registering instruments, ingesting OHLCV price data,
    and retrieving historical market data from Supabase.

    Assumptions:
    - Supabase tables `instruments` and `prices` already exist
    - UNIQUE constraint on instruments.symbol
    - UNIQUE constraint on prices (instrument_id, date)
    - RLS disabled OR service-role key is used
    - getData() returns DataFrame indexed by datetime with
      Open, High, Low, Close, Volume columns
    """

    def __init__(self, supabase_url: str, supabase_key: str):
        if not supabase_url or not supabase_key:
            raise ValueError("Supabase URL or Key missing")

        self.supabase: Client = create_client(supabase_url, supabase_key)
        self._instrument_cache: Dict[str, int] = {}

    # ------------------------------------------------------------------
    # Instrument Registration
    # ------------------------------------------------------------------

    def register(self, instruments: Union[dict, List[dict]]) -> List[int]:
        """
        Register one or multiple instruments with metadata.
        Idempotent: existing symbols are updated with new metadata.

        Parameters
        ----------
        instruments : dict | list[dict]
            Instrument(s) to register. Each dict must contain 'symbol'.
            Optional keys: name, exchange, asset_class, instrument_type

        Returns
        -------
        list[int]
            Instrument IDs (existing or newly created)

        Raises
        ------
        ValueError
            If instrument dict is missing 'symbol' key
        """
        if isinstance(instruments, dict):
            instruments = [instruments]

        if not instruments:
            return []

        # Validate all instruments have symbols
        for inst in instruments:
            if "symbol" not in inst:
                raise ValueError("Each instrument must have a 'symbol' key")

        symbols = [inst["symbol"] for inst in instruments]

        # Batch fetch existing instruments
        try:
            resp = (
                self.supabase.table("instruments")
                .select("id, symbol")
                .in_("symbol", symbols)
                .execute()
            )
            
            existing = {row["symbol"]: row["id"] for row in resp.data} if resp.data else {}
        except Exception as e:
            logger.error(f"Failed to fetch existing instruments: {e}")
            raise

        ids: List[int] = []
        to_insert: List[dict] = []
        to_update: List[dict] = []

        for inst in instruments:
            symbol = inst["symbol"]
            
            payload = {
                "symbol": symbol,
                "name": inst.get("name", symbol),
                "exchange": inst.get("exchange"),
                "asset_class": inst.get("asset_class"),
                "instrument_type": inst.get("instrument_type"),
            }

            if symbol in existing:
                # Update existing instrument
                inst_id = existing[symbol]
                ids.append(inst_id)
                to_update.append({"id": inst_id, **payload})
                # Update cache
                self._instrument_cache[symbol] = inst_id
            else:
                # New instrument
                to_insert.append(payload)

        # Batch insert new instruments
        if to_insert:
            try:
                resp = self.supabase.table("instruments").insert(to_insert).execute()
                for row in resp.data:
                    ids.append(row["id"])
                    self._instrument_cache[row["symbol"]] = row["id"]
                logger.info(f"Registered {len(to_insert)} new instruments")
            except Exception as e:
                logger.error(f"Failed to insert instruments: {e}")
                raise

        # Batch update existing instruments
        if to_update:
            try:
                for update in to_update:
                    self.supabase.table("instruments").update(update).eq("id", update["id"]).execute()
                logger.info(f"Updated {len(to_update)} existing instruments")
            except Exception as e:
                logger.error(f"Failed to update instruments: {e}")
                raise

        return ids

    def get_instrument_id(self, symbol: str) -> Optional[int]:
        """
        Get instrument ID for a symbol.

        Parameters
        ----------
        symbol : str
            Instrument symbol

        Returns
        -------
        int | None
            Instrument ID if found, None otherwise
        """
        # Check cache first
        if symbol in self._instrument_cache:
            return self._instrument_cache[symbol]

        # Query database
        try:
            resp = (
                self.supabase.table("instruments")
                .select("id")
                .eq("symbol", symbol)
                .maybe_single()
                .execute()
            )

            if resp.data:
                inst_id = resp.data["id"]
                self._instrument_cache[symbol] = inst_id
                return inst_id
            return None
        except Exception as e:
            logger.error(f"Failed to fetch instrument ID for {symbol}: {e}")
            raise

    def list_instruments(
        self, 
        symbols: Optional[Union[str, List[str]]] = None,
        exchange: Optional[str] = None,
        asset_class: Optional[str] = None
    ) -> pd.DataFrame:
        """
        List registered instruments with optional filters.

        Parameters
        ----------
        symbols : str | list[str], optional
            Filter by specific symbol(s)
        exchange : str, optional
            Filter by exchange
        asset_class : str, optional
            Filter by asset class

        Returns
        -------
        DataFrame
            Registered instruments with metadata
        """
        try:
            query = self.supabase.table("instruments").select("*")

            if symbols is not None:
                if isinstance(symbols, str):
                    symbols = [symbols]
                query = query.in_("symbol", symbols)
            if exchange:
                query = query.eq("exchange", exchange)
            if asset_class:
                query = query.eq("asset_class", asset_class)

            resp = query.order("symbol").execute()

            if not resp.data:
                return pd.DataFrame()

            return pd.DataFrame(resp.data)
        except Exception as e:
            logger.error(f"Failed to list instruments: {e}")
            raise

    # ------------------------------------------------------------------
    # Historical Data Ingestion
    # ------------------------------------------------------------------

    def load_history(
        self,
        symbols: Union[str, List[str]],
        start_date: str,
        end_date: Optional[str] = None,
    ) -> Dict[str, int]:
        """
        Load historical OHLCV data for one or multiple symbols.
        
        All symbols MUST be registered before loading data.
        Use register() first to add instruments with metadata.

        Parameters
        ----------
        symbols : str | list[str]
            Symbol(s) to load data for (must be pre-registered)
        start_date : str
            Start date in YYYY-MM-DD format
        end_date : str, optional
            End date in YYYY-MM-DD format (defaults to today)

        Returns
        -------
        dict
            {symbol: num_records_loaded}

        Raises
        ------
        ValueError
            If any symbol is not registered
        """
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")

        # Normalize to list
        if isinstance(symbols, str):
            symbols = [symbols]

        # Validate all symbols are registered
        symbol_to_id: Dict[str, int] = {}
        missing_symbols: List[str] = []

        for symbol in symbols:
            inst_id = self.get_instrument_id(symbol)
            if inst_id is None:
                missing_symbols.append(symbol)
            else:
                symbol_to_id[symbol] = inst_id

        if missing_symbols:
            raise ValueError(
                f"Instruments not registered: {missing_symbols}. "
                f"Use register() to add them first."
            )

        # Load data for each symbol
        results: Dict[str, int] = {}

        for symbol, inst_id in symbol_to_id.items():
            try:
                # Fetch market data
                df = getData(symbol, start_date=start_date, end_date=end_date)

                if df.empty:
                    logger.warning(f"No data available for {symbol}")
                    results[symbol] = 0
                    continue

                # Prepare rows with NaN handling
                rows = []
                for idx, row in df.iterrows():
                    try:
                        rows.append({
                            "instrument_id": inst_id,
                            "date": idx.strftime("%Y-%m-%d"),
                            "open": float(row["Open"]) if pd.notna(row["Open"]) else None,
                            "high": float(row["High"]) if pd.notna(row["High"]) else None,
                            "low": float(row["Low"]) if pd.notna(row["Low"]) else None,
                            "close": float(row["Close"]) if pd.notna(row["Close"]) else None,
                            "volume": int(row["Volume"]) if pd.notna(row["Volume"]) else 0,
                        })
                    except (ValueError, KeyError) as e:
                        logger.warning(f"Skipping invalid row for {symbol} at {idx}: {e}")
                        continue

                if not rows:
                    logger.warning(f"No valid data rows for {symbol}")
                    results[symbol] = 0
                    continue

                # Upsert OHLCV data
                self.supabase.table("prices").upsert(
                    rows, on_conflict="instrument_id,date"
                ).execute()

                results[symbol] = len(rows)
                logger.info(f"Loaded {len(rows)} records for {symbol}")

            except Exception as e:
                logger.error(f"Failed to load data for {symbol}: {e}")
                results[symbol] = -1  # Indicate failure

        return results

    # ------------------------------------------------------------------
    # Data Retrieval
    # ------------------------------------------------------------------

    def get_prices(
        self,
        symbols: Optional[Union[str, List[str]]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> pd.DataFrame:
        """
        Retrieve OHLCV data in long format.

        Parameters
        ----------
        symbols : str | list[str], optional
            Filter by symbol(s). If None, returns all.
        start_date : str, optional
            Start date filter (YYYY-MM-DD)
        end_date : str, optional
            End date filter (YYYY-MM-DD)
        limit : int, optional
            Maximum number of records to return

        Returns
        -------
        DataFrame
            Columns: date, open, high, low, close, volume, symbol
            Sorted by date ascending
        """
        try:
            query = self.supabase.table("prices").select(
                "date, open, high, low, close, volume, instruments!inner(symbol)"
            )

            if symbols is not None:
                if isinstance(symbols, str):
                    symbols = [symbols]
                query = query.in_("instruments.symbol", symbols)

            if start_date:
                query = query.gte("date", start_date)
            if end_date:
                query = query.lte("date", end_date)

            query = query.order("date", desc=False)

            if limit:
                query = query.limit(limit)

            resp = query.execute()

            if not resp.data:
                return pd.DataFrame(
                    columns=["date", "open", "high", "low", "close", "volume", "symbol"]
                )

            df = pd.DataFrame(resp.data)

            # Extract symbol from joined table
            df["symbol"] = df["instruments"].apply(lambda x: x["symbol"])
            df = df.drop(columns=["instruments"])

            # Convert date to datetime
            df["date"] = pd.to_datetime(df["date"])

            return df

        except Exception as e:
            logger.error(f"Failed to retrieve prices: {e}")
            raise

    def get_asset_prices(
        self,
        symbols: Optional[Union[str, List[str]]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        column: str = "close",
    ) -> pd.DataFrame:
        """
        Retrieve OHLCV data in wide format (symbols as columns).

        Parameters
        ----------
        symbols : str | list[str], optional
            Filter by symbol(s)
        start_date : str, optional
            Start date filter (YYYY-MM-DD)
        end_date : str, optional
            End date filter (YYYY-MM-DD)
        column : str
            Price column to pivot ('open', 'high', 'low', 'close', 'volume')

        Returns
        -------
        DataFrame
            Index: date, Columns: symbols
        """
        df = self.get_prices(symbols, start_date, end_date)

        if df.empty:
            return pd.DataFrame()

        # Pivot to wide format
        df_wide = df.pivot(index="date", columns="symbol", values=column)

        return df_wide

    def get_latest_prices(
        self, symbols: Optional[Union[str, List[str]]] = None
    ) -> pd.DataFrame:
        """
        Get the most recent price for each symbol.

        Parameters
        ----------
        symbols : str | list[str], optional
            Filter by symbol(s)

        Returns
        -------
        DataFrame
            Latest price record for each symbol
        """
        try:
            # Build subquery for max date per instrument
            if symbols:
                if isinstance(symbols, str):
                    symbols = [symbols]
                
                # Get instrument IDs
                inst_resp = (
                    self.supabase.table("instruments")
                    .select("id, symbol")
                    .in_("symbol", symbols)
                    .execute()
                )
                
                if not inst_resp.data:
                    return pd.DataFrame()
                
                instrument_ids = [row["id"] for row in inst_resp.data]
                symbol_map = {row["id"]: row["symbol"] for row in inst_resp.data}
            else:
                # Get all instruments
                inst_resp = self.supabase.table("instruments").select("id, symbol").execute()
                if not inst_resp.data:
                    return pd.DataFrame()
                
                instrument_ids = [row["id"] for row in inst_resp.data]
                symbol_map = {row["id"]: row["symbol"] for row in inst_resp.data}

            # Get latest price for each instrument
            all_latest = []
            for inst_id in instrument_ids:
                resp = (
                    self.supabase.table("prices")
                    .select("*")
                    .eq("instrument_id", inst_id)
                    .order("date", desc=True)
                    .limit(1)
                    .execute()
                )
                
                if resp.data:
                    record = resp.data[0]
                    record["symbol"] = symbol_map[inst_id]
                    all_latest.append(record)

            if not all_latest:
                return pd.DataFrame()

            df = pd.DataFrame(all_latest)
            df["date"] = pd.to_datetime(df["date"])
            df = df.drop(columns=["instrument_id"])

            return df[["symbol", "date", "open", "high", "low", "close", "volume"]]

        except Exception as e:
            logger.error(f"Failed to retrieve latest prices: {e}")
            raise