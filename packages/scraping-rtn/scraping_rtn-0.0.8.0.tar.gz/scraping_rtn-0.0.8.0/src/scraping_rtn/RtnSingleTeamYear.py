from .src import EVENT_MAP, EVENTS, get_session, get_data_from_api, fix_opponents, normalize_date, merge_dicts, \
    get_extra_cols, SCHEDULE_COLS, RESULTS_COLS, IND_RESULTS_COLS, ROSTER_COLS
import pandas as pd
import numpy as np
from datetime import datetime


class RtnSingleTeamYear(object):
    def __init__(self, year, team_name, team_id=None, session=None):
        self.year = year
        if team_name is not None:
            self.team_name = team_name
            if team_id is None:
                self.team_id = self.get_team_id()
            else:
                self.team_id = team_id

        if session is None:
            self.session = get_session()
        else:
            self.session = session

    def get_team_mapping(self, force_update=False):
        if force_update:
            get_data_from_api.cache_clear()

        all_teams_data = get_data_from_api(endpoint='gymnasts2', suffix=str(self.year) + '/1', session=self.session).json()
        return {team['team_name']: team['id'] for team in all_teams_data['teams']}

    def get_team_id(self):
        if not hasattr(self, 'team_id_map'):
            self.team_id_map = self.get_team_mapping()

        if self.team_name and self.team_name not in self.team_id_map.keys():
            raise ValueError(f'Unknown team name: {self.team_name}')

        return self.team_id_map.get(self.team_name, -1)
        # if self.team_name in self.team_id_map.keys():
        #     return self.team_id_map[self.team_name]
        # else:
        #     raise ValueError(f'{self.team_name} does not exist in data for {self.year}')

    def _get_raw_roster(self, force_update=False):
        rename_map = {'id': 'Gymnast ID', 'hometown': 'Hometown', 'school_year': 'School Year', 'events': 'Events'}
        school_year_map = {'1': 'FR', '2': 'SO', '3': 'JR', '4': 'SR'}

        if force_update:
            get_data_from_api.cache_clear()

        roster_data = get_data_from_api(endpoint='rostermain', suffix=str(self.year)+'/'+str(self.team_id)+'/1', session=self.session).json()

        self._raw_roster = [{**{rename_map.get(k, k): v if k != 'school_year' else school_year_map.get(v, '') for k, v in data.items()},
                            **{'Name': data['fname'] + ' ' + data['lname'], 'Team': self.team_name}}
                            for data in roster_data]

    def get_roster(self, include_hometowns=False, include_class=False, include_events=False, force_update=False):
        if not hasattr(self, 'raw_roster'):
            self._get_raw_roster(force_update=force_update)

        extra_cols = get_extra_cols(include_hometowns=include_hometowns, include_class=include_class, include_events=include_events)

        if len(self._raw_roster) > 0:
            self.roster = pd.DataFrame([{k: v for k, v in data.items() if k in ROSTER_COLS + extra_cols}
                                        for data in self._raw_roster])
        else:
            self.roster = pd.DataFrame(columns=ROSTER_COLS + extra_cols)

        return self.roster

    def _get_raw_season_results(self, force_update=False):
        if force_update:
            get_data_from_api.cache_clear()

        meets = get_data_from_api(endpoint='dashboard', suffix=str(self.year)+'/'+str(self.team_id), session=self.session).json()
        name_map = {'team_id': 'Team ID', 'team_name': 'Team', 'meet_id': 'Team Meet ID',
                    'meet_date': 'Meet Date', 'team_score': 'Score', 'home': 'Home/Away',
                    'opponent': 'Opponents', 'meet_desc': 'Meet Name', 'linked_id': 'Meet ID'}

        self._raw_season_results = [{name_map.get(k, k): fix_opponents(v) if k == 'opponent'
                                    else (normalize_date(v) if k == 'meet_date' else v)
                                     for k, v in data.items() if k != 'jas'} for data in meets['meets'] if data['team_name'] == self.team_name]
        self._raw_schedule = [{k: v for k, v in data.items() if k not in ('Score', 'VT', 'UB', 'BB', 'FX')} for data in self._raw_season_results]

    def get_schedule(self, force_update=False):
        if not hasattr(self, '_raw_schedule'):
            self._get_raw_season_results(force_update=force_update)

        if len(self._raw_schedule) > 0:
            return pd.DataFrame(self._raw_schedule)
        else:
            return pd.DataFrame(columns=SCHEDULE_COLS)

    def get_team_scores(self, method='team_consistency', force_update=False):
        """
        Methods:
        * Team Consistency - uses the Team Consistency tab from RTN.
            * Only a single API call for all meets so much faster
            * Tends to have more complete data, especially for older years
            * Does not include meets (like event finals) where only individuals compete
            * Relies on date to join back to meet info, such as opponent, etc.
        * By Meet - loops through each meet to get scores
            * One API call per meet, so much slower
            * Older meets tend to be missing
            * Includes individual scores from meets where whole team did not compete
            * Uses team meet id to join back to meet info, such as opponent, etc.
        """
        if not hasattr(self, '_raw_season_results'):
            self._get_raw_season_results(force_update=force_update)

        if len(self._raw_season_results) > 0:
            if (len({'VT', 'UB', 'BB', 'FX'}.intersection(self._raw_season_results[0].keys())) != 4 or force_update):
                if method == 'team_consistency':
                    self._team_event_scores_team_consistency(force_update=force_update)
                elif method == 'by_meet':
                    self._team_event_scores_by_meet(force_update=force_update)
                else:
                    raise ValueError('Method must be "team_consistency" or "by_meet"')

            # TODO: different way to drop duplicates?
            self.season_results = pd.DataFrame(self._raw_season_results).dropna(subset=['Score']).drop_duplicates()
        else:
            self.season_results = pd.DataFrame(columns=SCHEDULE_COLS + RESULTS_COLS)

        return self.season_results

    def _team_event_scores_by_meet(self, force_update=False):
        team_scores_all = []
        for meet_id in [data['Team Meet ID'] for data in self._raw_season_results if data['Meet Date'] <= datetime.now()]:
            try:
                if force_update:
                    get_data_from_api.cache_clear()

                meet_res = get_data_from_api(endpoint='meetresults', suffix=str(meet_id), session=self.session).json()
                # This API call returns scores from all teams at this meet, not just this team. Need to pick out correct score
                team_scores = [score for score in meet_res['teams'] if score['tname'] == self.team_name and score['mid'] == str(meet_id)]
                assert len(team_scores) == 1, 'Multiple team scores??'
                team_scores_all.append({EVENT_MAP.get(k, 'Team Meet ID'): v for k, v in team_scores[0].items() if k in ['mid', 'vault', 'bars', 'beam', 'floor']})
            except ValueError:
                print(f'Meet {meet_id} not found')

        if len(team_scores_all) > 0:
            merge_dicts(dict1=self._raw_season_results, dict2=team_scores_all, merge_field='Team Meet ID')
        else:
            print(f'No meet data found for year {self.year}')
            for i in range(len(self._raw_season_results)):
                self._raw_season_results[i].update({'VT': np.nan, 'UB': np.nan, 'BB': np.nan, 'FX': np.nan})

    def _team_event_scores_team_consistency(self, force_update=False):
        if force_update:
            get_data_from_api.cache_clear()

        res = get_data_from_api(endpoint='teamConsistency', suffix=f'{self.year}/{self.team_id}', session=self.session).json()
        if len(res['labels']) == 0:
            print(f'No team consistency data found for {self.team_name} in {self.year}')
            for i in range(len(self._raw_season_results)):
                self._raw_season_results[i].update({'VT': np.nan, 'UB': np.nan, 'BB': np.nan, 'FX': np.nan})
        else:

            team_consistency = [{'Meet Date': normalize_date(res['labels'][i][:7] + str(self.year), dt_format='%b-%d-%Y'),
                                 'VT': round(float(res['vts'][i]), 4),
                                 'UB': round(float(res['ubs'][i]), 4),
                                 'BB': round(float(res['bbs'][i]), 4),
                                 'FX': round(float(res['fxs'][i]), 4)} for i in range(len(res['labels']))]

            merge_dicts(dict1=self._raw_season_results, dict2=team_consistency, merge_field='Meet Date')

    def get_individual_scores(self, method='individual_consistency', force_update=False):
        """
        Methods:
        * Individual Consistency - Uses Individual Consistency tab from RTN
            * Tends to have more complete data, especially for older years
            * Relies on date to join back to meet info, such as opponent, etc.
            * One API call per gymnast, relative speed depends on number of meets vs number of gymnasts
        * By Meet - loops through each meet to get scores
            * Older meets tend to be missing
            * Uses team meet id to join back to meet info, such as opponent, etc.
            * One API call per meet, relative speed depends on number of meets vs number of gymnasts
        """
        if not hasattr(self, '_raw_schedule'):
            self.get_schedule()

        if force_update or not hasattr(self, 'individual_results'):
            if method == 'individual_consistency':
                if not hasattr(self, '_raw_roster'):
                    self.get_roster()

                self._individual_scores_individual_consistency(force_update=force_update)
            elif method == 'by_meet':
                self._individual_scores_by_meet(force_update=force_update)
            else:
                raise ValueError('Method must be "individual_consistency" or "by_meet"')

        return self.individual_results

    def _individual_scores_by_meet(self, force_update=False):
        individual_scores_all = []
        for meet_id in [meet['Team Meet ID'] for meet in self._raw_schedule if meet['Meet Date'] <= datetime.now()]:
            try:
                if force_update:
                    get_data_from_api.cache_clear()

                meet_res = get_data_from_api(endpoint='meetresults', suffix=str(meet_id), session=self.session).json()
                if len(meet_res) == 0 or len(meet_res['scores']) == 0 or len(meet_res['scores'][0]) == 0:
                    print(f'No data found for meet {meet_id}')
                    continue

                if 'team_name' in meet_res['scores'][0][0]:
                    team_inds = [ind for ind, scores in enumerate(meet_res['scores']) if len(scores) > 0 and scores[0]['team_name'] == self.team_name]
                else:
                    raise ValueError('Key not found')

                if len(team_inds) == 0:
                    print(f'No scores found at meet {meet_id}')
                    continue
                team_ind = team_inds[0]

                individual_scores = [{**{EVENT_MAP.get(k, {'gid': 'Gymnast ID'}.get(k, k)):
                                         v if k not in EVENT_MAP.keys() else (round(float(v), 4) if v is not None else np.nan)
                                         for k, v in data.items() if k in ['gid'] + list(EVENT_MAP.keys())},
                                      **{'Team Meet ID': str(meet_id),
                                         'Name': data['first_name'] + ' ' + data['last_name']}}
                                     for data in meet_res['scores'][team_ind]]

                individual_scores_all.extend(individual_scores)
            except ValueError:
                print(f'Meet {meet_id} not found')

        if len(individual_scores_all) > 0:
            merge_dicts(dict1=individual_scores_all, dict2=self._raw_schedule, merge_field='Team Meet ID')
            self.individual_results = pd.DataFrame(individual_scores_all)
            self.individual_results['AA'] = self.individual_results[['VT', 'UB', 'BB', 'FX']].dropna(how='any').astype(float).T.sum().round(4)
        else:
            self.individual_results = pd.DataFrame(columns=['Meet Date', 'VT', 'UB', 'BB', 'FX', 'AA', 'Gymnast ID', 'Name',
                                                    'Team ID', 'Team', 'Team Meet ID', 'Home/Away', 'Opponents',
                                                    'Meet Name', 'Meet ID'])

    def _individual_scores_individual_consistency(self, force_update=False):
        ind_consistency_all = []
        for gymnast in self._raw_roster:
            try:
                if force_update:
                    get_data_from_api.cache_clear()

                res = get_data_from_api(endpoint='indConsistency', suffix=f"{self.year}/{gymnast['Gymnast ID']}", session=self.session).json()
                ind_consistency = [{'Meet Date': normalize_date(res['labels'][i][:7] + str(self.year), dt_format='%b-%d-%Y'),
                                    'VT': round(float(res['vts'][i]), 4) if res['vts'][i] is not None else np.nan,
                                    'UB': round(float(res['ubs'][i]), 4) if res['ubs'][i] is not None else np.nan,
                                    'BB': round(float(res['bbs'][i]), 4) if res['bbs'][i] is not None else np.nan,
                                    'FX': round(float(res['fxs'][i]), 4) if res['fxs'][i] is not None else np.nan,
                                    'AA': round(float(res['vts'][i]) + float(res['ubs'][i]) + float(res['bbs'][i]) + float(res['fxs'][i]), 4) if all([res['vts'][i],res['ubs'][i],res['bbs'][i],res['fxs'][i]]) else np.nan,
                                    'Gymnast ID': gymnast['Gymnast ID'],
                                    'Name': gymnast['Name']
                                    } for i in range(len(res['labels']))]
                ind_consistency_all.extend(ind_consistency)

            except ValueError:
                print(f"No individual consistency scores found for {gymnast['Name']}")

        if len(ind_consistency_all) > 0:
            merge_dicts(dict1=ind_consistency_all, dict2=self._raw_schedule, merge_field='Meet Date')
            self.individual_results = pd.DataFrame(ind_consistency_all)
        else:
            self.individual_results = pd.DataFrame(columns=SCHEDULE_COLS + IND_RESULTS_COLS)

    def get_individual_nqs(self, force_update=False):
        if not hasattr(self, '_raw_roster'):
            self._get_raw_roster(force_update=force_update)

        if not hasattr(self, '_raw_individual_nqs'):
            self._get_raw_individual_nqs(force_update=force_update)

        if len(self._raw_individual_nqs) > 0:
            return pd.DataFrame(self._raw_individual_nqs)
        else:
            return pd.DataFrame(columns=ROSTER_COLS + EVENTS) # + ['AA'])

    def _get_raw_individual_nqs(self, force_update=False):
        name_map = {'maxv': 'VT', 'maxub': 'UB', 'maxbb': 'BB', 'maxfx': 'FX',
                    # 'maxaa': 'AA',
                    'gid': 'Gymnast ID'}
        if force_update:
            get_data_from_api.cache_clear()

        nqsData = get_data_from_api(endpoint='rostermain', suffix=f'{self.year}/{self.team_id}/4', session=self.session).json()
        ind_nqs = [{name_map[k]: round(float(v), 4) if k != 'gid' and v != '' else (np.nan if k != 'gid' else v)
                    for k, v in data.items() if k in name_map.keys()} for data in nqsData['ind']]

        if len(ind_nqs) > 0:
            self._raw_individual_nqs = [{k: v for k, v in data.items() if k in ['Gymnast ID', 'Name', 'Team']}
                                        for data in self._raw_roster]
            merge_dicts(dict1=self._raw_individual_nqs, dict2=ind_nqs, merge_field='Gymnast ID')
        else:
            self._raw_individual_nqs = []

    def _get_current_week(self, force_update=False):
        if not hasattr(self, 'week'):
            if force_update:
                get_data_from_api.cache_clear()

            week_data = get_data_from_api(endpoint='currentweek', suffix=str(self.year), session=self.session).json()
            return min(int(week_data['week']), int(week_data['max']))

    def _get_raw_rankings(self, team_vs_ind, event, week, force_update=False):
        team_ind_map = {'team': 0, 'ind': 1}
        event_api_map = {'VT': 1, 'UB': 2, 'BB': 3, 'FX': 4, 'AA': 5}
        rename_map = {'rank': 'Rank', 'gid': 'Gymnast ID', 'team': 'Team', 'tid': 'Team ID',
                      'rqs': 'NQS', 'reg': 'Region', 'con': 'Conference', 'div': 'Division',
                      'usag': 'USAG', 'ave': 'Average', 'high': 'High', 'name': 'Team'}

        if force_update:
            get_data_from_api.cache_clear()

        res = get_data_from_api(endpoint='results', suffix=f'{self.year}/{week}/{team_ind_map[team_vs_ind]}/{event_api_map[event]}', session=self.session).json()
        if team_vs_ind == 'ind':
            self._raw_rankings[team_vs_ind][event] = [{**{rename_map.get(k): float(v) if k in ['rqs', 'ave', 'high'] else v for k, v in data.items() if k in rename_map},
                                                       **{'Name': data['fname'] + ' ' + data['lname'], 'Event': event}}
                                                      for data in res['data']]
        else:
            self._raw_rankings[team_vs_ind][event] = [{**{rename_map.get(k): float(v) if k in ['rqs', 'ave', 'high'] else v for k, v in data.items() if k in rename_map},
                                                       **{'Event': event}}
                                                      for data in res['data']]

    def get_overall_rankings(self, team_vs_ind='team', event='AA', week=None, force_update=False):
        if not week:
            week = self._get_current_week(force_update=force_update)

        if not hasattr(self, '_raw_rankings'):
            self._raw_rankings = {'team': {event: None for event in EVENT_MAP.values()},
                                  'ind': {event: None for event in EVENT_MAP.values()}}

        col_orders = {'ind': ['Event', 'Rank', 'Gymnast ID', 'Name', 'Team ID', 'Team', 'NQS', 'Average', 'High',
                              'Division', 'Conference', 'Region', 'USAG'],
                      'team': ['Event', 'Rank', 'Team ID', 'Team', 'NQS', 'Average', 'High',
                               'Division', 'Conference', 'Region', 'USAG']}

        if self._raw_rankings[team_vs_ind][event] is None:
            self._get_raw_rankings(team_vs_ind=team_vs_ind, event=event, week=week, force_update=force_update)

        return pd.DataFrame(self._raw_rankings[team_vs_ind][event])[col_orders[team_vs_ind]]


