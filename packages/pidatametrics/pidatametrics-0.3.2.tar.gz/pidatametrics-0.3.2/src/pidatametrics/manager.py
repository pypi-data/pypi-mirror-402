from .client import PiDataMetrics
from .parsers import PiParsers
from .exporter import PiExporter
import datetime
from dateutil.relativedelta import relativedelta

class PiReportManager(PiDataMetrics):
    def _resolve_workspaces(self, ids_str=None, name_pattern=None):
        all_ws = self.get_workspaces()
        targets = {}
        if ids_str and ids_str.strip():
            target_ids = [int(x.strip()) for x in ids_str.split(',') if x.strip().isdigit()]
            for ws in all_ws:
                if ws['id'] in target_ids:
                    targets[ws['id']] = ws['name']
        elif name_pattern:
            for ws in all_ws:
                if ws.get('tracked') and name_pattern.lower() in ws['name'].lower():
                    targets[ws['id']] = ws['name']
        return targets

    def _generate_historical_dates(self, start_date_str, duration, frequency):
        dates = []
        try:
            current_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d")
        except ValueError:
            print(f"Error: Invalid date format {start_date_str}. Using yesterday.")
            current_date = datetime.datetime.now() - datetime.timedelta(days=1)
        if current_date > datetime.datetime.now():
            print(f"WARNING: Start date {current_date.strftime('%Y-%m-%d')} is in the future!")
        if frequency == 'weekly':
            days_since_sunday = (current_date.weekday() + 1) % 7
            if days_since_sunday > 0:
                current_date -= datetime.timedelta(days=days_since_sunday)
                print(f"Note: Adjusted start date to previous Sunday: {current_date.strftime('%Y-%m-%d')}")
        for _ in range(int(duration)):
            dates.append(current_date.strftime("%Y-%m-%d"))
            if frequency == 'daily':
                current_date -= datetime.timedelta(days=1)
            elif frequency == 'weekly':
                current_date -= datetime.timedelta(weeks=1)
            elif frequency == 'monthly':
                current_date -= relativedelta(months=1)
        return dates

    def run_volume_report(self, filename, workspace_ids=None, workspace_name=None, output_mode='csv', bq_config=None):
        targets = self._resolve_workspaces(workspace_ids, workspace_name)
        if not targets: return
        all_rows = []
        for ws_id, ws_name in targets.items():
            vol_data = self.get_bulk_volume(ws_id)
            stgs = self.get_stgs(ws_id)
            for stg in stgs:
                terms = self.get_search_terms(ws_id, stg['id'])
                rows = PiParsers.parse_volume_data(vol_data, stg['name'], terms, ws_name)
                all_rows.extend(rows)
        
        if output_mode == 'bigquery' and bq_config:
            PiExporter.to_bigquery(all_rows, bq_config['project'], bq_config['dataset'], bq_config['table'])
        else:
            PiExporter.to_csv(all_rows, filename)

    def run_serp_report(self, data_sources, output_mode='csv', bq_config=None, filename=None, manual_duplication=None):
        yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        all_rows = []
        for source in data_sources:
            market, w_id, w_name, se_id, se_name = source
            raw_data = self.get_bulk_serp_data(w_id, se_id, yesterday)
            cat_map = PiParsers.build_category_map(self, w_id)
            rows = PiParsers.parse_serp_response(raw_data, market, w_name, se_name, yesterday, cat_map, manual_duplication)
            all_rows.extend(rows)
        
        if output_mode == 'bigquery' and bq_config:
            PiExporter.to_bigquery(all_rows, bq_config['project'], bq_config['dataset'], bq_config['table'])
        else:
            PiExporter.to_csv(all_rows, filename or "serp_output.csv")

    def run_historical_serp_report(self, data_sources, duration, frequency, start_date=None, features=None, num_results=25, output_mode='csv', bq_config=None, filename="historical_data.csv"):
        if features is None:
            features = ['classicLink', 'popularProducts']

        if not start_date:
            start_date = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")

        target_dates = self._generate_historical_dates(start_date, duration, frequency)
        
        print(f"Starting Historical Report ({frequency}) for last {duration} periods...")
        
        all_csv_rows = [] # Only used if output_mode is CSV

        for i, date in enumerate(target_dates):
            print(f"[{i+1}/{len(target_dates)}] Processing Date: {date}...")
            
            daily_rows = [] # Reset container for this specific date

            for source in data_sources:
                market, w_id, w_name, se_id, se_name = source
                try:
                    params = {
                        'serp-feature[]': features,
                        'number-of-results': num_results
                    }
                    raw_data = self.get_bulk_serp_data(w_id, se_id, date, **params)
                    
                    # Parser handles filtering null titles
                    rows = PiParsers.parse_serp_response(
                        raw_data, market, w_name, se_name, date, category_map=None
                    )
                    
                    daily_rows.extend(rows)

                except Exception as e:
                    print(f"Failed to fetch {w_name} on {date}: {e}")

            # --- UPLOAD LOGIC: PER DATE ---
            if output_mode == 'bigquery' and bq_config:
                if daily_rows:
                    print(f"Uploading {len(daily_rows)} rows for {date} to BigQuery...")
                    PiExporter.to_bigquery(daily_rows, bq_config['project'], bq_config['dataset'], bq_config['table'])
                else:
                    print(f"No data found for {date}, skipping upload.")
            
            # --- CSV LOGIC: ACCUMULATE ---
            elif output_mode == 'csv':
                all_csv_rows.extend(daily_rows)

        # Final Save for CSV only
        if output_mode == 'csv':
            PiExporter.to_csv(all_csv_rows, filename)

    # --- NEW: LLM Report ---
    def run_llm_report(self, data_sources, start_period, end_period, stg_ids=None, output_mode='csv', bq_config=None, filename="llm_output.csv"):
        """
        Runs the LLM Mentions report for the specified data sources and date range.
        
        :param data_sources: List of tuples (market, workspace_id, workspace_name, search_engine_id, search_engine_name)
        :param start_period: YYYY-MM-DD or YYYY-WWW
        :param end_period: YYYY-MM-DD or YYYY-WWW
        :param stg_ids: Optional list of integers to filter by Search Term Group
        """
        all_rows = []
        print(f"Starting LLM Report from {start_period} to {end_period}...")

        for source in data_sources:
            market, w_id, w_name, se_id, se_name = source
            try:
                print(f"Fetching LLM data for {w_name} ({se_name})...")
                raw_data = self.get_llm_mentions(w_id, se_id, start_period, end_period, stg_ids)
                
                rows = PiParsers.parse_llm_response(raw_data, market, w_name, se_name)
                all_rows.extend(rows)
                print(f"Found {len(rows)} mentions/queries.")
            except Exception as e:
                print(f"Failed to fetch LLM data for {w_name}: {e}")

        if output_mode == 'bigquery' and bq_config:
            PiExporter.to_bigquery(all_rows, bq_config['project'], bq_config['dataset'], bq_config['table'])
        else:
            PiExporter.to_csv(all_rows, filename)