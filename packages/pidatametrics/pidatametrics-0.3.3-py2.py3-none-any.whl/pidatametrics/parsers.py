import json

class PiParsers:
    @staticmethod
    def parse_serp_response(raw_data, market, workspace_name, search_engine_name, date, category_map=None, manual_duplication=None):
        """
        Transforms the nested 'Bulk Search Results' JSON into a flat list of dicts.
        """
        flat_rows = []
        
        for item in raw_data:
            search_term = item.get('searchTerm')
            
            category = ""
            if category_map:
                category = category_map.get(search_term, "")

            results = item.get('results', [])
            previous_pos = None

            if results:
                for res in results:
                    feature_type = res.get('feature')
                    title = res.get('title')

                    # If feature is popularProducts AND title is null/empty, SKIP this row.
                    if feature_type == 'popularProducts' and not title:
                        continue 

                    # --- Logic for Position Fill-Down ---
                    pos = res.get('position')
                    if pos is None:
                        pos = previous_pos
                    
                    # --- Logic for Attributes (Popular Products) ---
                    attributes = res.get('attributes', {})
                    price = None
                    site_name = None
                    
                    if isinstance(attributes, dict):
                        price = attributes.get('price')
                        site_name = attributes.get('site')
                        attr_str = json.dumps(attributes)
                    else:
                        attr_str = None

                    # Create Row
                    row = {
                        'Date': date,
                        'Market': market,
                        'SearchTerm': search_term,
                        'URL': res.get('url'),
                        'Position': pos,
                        'SERPFeature': feature_type,
                        'PageTitle': title,
                        'Price': price,
                        'SiteName': site_name,
                        'SearchEngine': search_engine_name,
                        'Attributes': attr_str,
                        'Category': category,
                        'Workspace': workspace_name
                    }
                    
                    flat_rows.append(row)
                    previous_pos = pos
            else:
                pass
                
        return flat_rows

    @staticmethod
    def parse_volume_data(volume_data, stg_name, stg_terms, workspace_name):
        rows = []
        volume_lookup = {item.get('search-term'): item for item in volume_data}

        for term in stg_terms:
            term_text = term if isinstance(term, str) else term.get('term', '')
            
            if term_text in volume_lookup:
                item = volume_lookup[term_text]
                cpc = item.get('cpc', '')
                monthly_volume = item.get('monthly-volume', {})
                
                for month, vol in monthly_volume.items():
                    rows.append({
                        "Workspace": workspace_name,
                        "STG": stg_name,
                        "Search Term": term_text,
                        "Month": month,
                        "Search Volume": vol,
                        "CPC": cpc
                    })
        return rows

    @staticmethod
    def build_category_map(pi_client, workspace_id):
        mapping = {}
        stgs = pi_client.get_stgs(workspace_id)
        for stg in stgs:
            terms = pi_client.get_search_terms(workspace_id, stg['id'])
            for term in terms:
                t_text = term if isinstance(term, str) else term.get('term')
                mapping[t_text] = stg['name']
        return mapping

    # --- NEW: LLM Parser ---
    @staticmethod
    def parse_llm_response(raw_data, market, workspace_name, search_engine_name):
        """
        Flattens LLM mentions data.
        Each mention becomes a row. If no mentions exist for a query, the query is still recorded.
        """
        rows = []
        for item in raw_data:
            period = item.get('period')
            query = item.get('query')
            response_text = item.get('response')
            mentions = item.get('mentions', [])

            base_row = {
                'Period': period,
                'Market': market,
                'Workspace': workspace_name,
                'SearchEngine': search_engine_name,
                'Query': query,
                'LLM_Response': response_text
            }

            if mentions:
                for m in mentions:
                    row = base_row.copy()
                    row.update({
                        'Entity': m.get('entity'),
                        'Citation': m.get('citation'),
                        'Source_Site': m.get('source_site'),
                        'Source_Domain': m.get('source_domain'),
                        'Source_URL': m.get('source_url'),
                        'Sentiment': m.get('sentiment'),
                        'Sentiment_Category': m.get('sentiment_category')
                    })
                    rows.append(row)
            else:
                # Record the query even if no citations found
                row = base_row.copy()
                row.update({
                    'Entity': None,
                    'Citation': None,
                    'Source_Site': None,
                    'Source_Domain': None,
                    'Source_URL': None,
                    'Sentiment': None,
                    'Sentiment_Category': None
                })
                rows.append(row)
        
        return rows