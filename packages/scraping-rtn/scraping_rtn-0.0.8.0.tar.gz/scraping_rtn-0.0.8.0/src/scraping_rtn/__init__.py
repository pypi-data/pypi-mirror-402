from .RtnSingleTeamYear import RtnSingleTeamYear
from .src import get_session, validate_input, get_extra_cols, SCHEDULE_COLS, RESULTS_COLS, IND_RESULTS_COLS, EVENTS, ROSTER_COLS
import pandas as pd

BLANK_SPACES = ' '*30


def save(df, filename):
    df.to_csv(filename, index=False)


def all_teams(year, force_update=False):
    rtn = RtnSingleTeamYear(year=year, team_name=None)
    return list(rtn.get_team_mapping(force_update=force_update).keys())


def roster(year, teams, include_hometowns=False, include_class=False, include_events=False, verbose=False, force_update=False):
    teams = validate_input(teams)
    session = get_session()

    all_rosters = []
    for i, team in enumerate(teams):
        if verbose:
            print(f'Getting roster for {team}{BLANK_SPACES}', end='\r' if team != teams[-1] else None)
        rtn = RtnSingleTeamYear(year=year, team_name=team, session=session)
        res = rtn.get_roster(include_hometowns=include_hometowns, include_class=include_class,
                             include_events=include_events, force_update=force_update if i == 0 else False)
        if verbose and len(res) == 0:
            print(f'\tNo roster found for {team}')
        all_rosters.append(res)

    extra_cols = get_extra_cols(include_hometowns=include_hometowns, include_class=include_class, include_events=include_events)
    return pd.concat(all_rosters)[ROSTER_COLS + extra_cols]


def schedule(year, teams, verbose=False, force_update=False):
    teams = validate_input(teams)
    session = get_session()

    all_schedules = []
    for i, team in enumerate(teams):
        if verbose:
            print(f'Getting schedule for {team}{BLANK_SPACES}', end='\r' if team != teams[-1] else None)
        rtn = RtnSingleTeamYear(year=year, team_name=team, session=session)
        res = rtn.get_schedule(force_update=force_update if i == 0 else False)
        if verbose and len(res) == 0:
            print(f'\tNo schedule found for {team}')
        all_schedules.append(res)

    return pd.concat(all_schedules)[SCHEDULE_COLS]


def team_results(year, teams, method='team_consistency', force_update=False, verbose=False):
    teams = validate_input(teams)
    session = get_session()
    
    all_results = []
    for i, team in enumerate(teams):
        if verbose:
            print(f'Getting schedule and results for {team}{BLANK_SPACES}', end='\r' if team != teams[-1] else None)
        rtn = RtnSingleTeamYear(year=year, team_name=team, session=session)
        res = rtn.get_team_scores(method=method, force_update=force_update if i == 0 else False)
        if verbose and len(res) == 0:
            print(f'\tNo schedule and results found for {team}')
        all_results.append(res)

    return pd.concat(all_results)[SCHEDULE_COLS + RESULTS_COLS]


def individual_results(year, teams, method='by_meet', force_update=False, verbose=False):
    teams = validate_input(teams)
    session = get_session()
    
    all_scores = []
    for i, team in enumerate(teams):
        if verbose:
            print(f'Getting scores for {team}{BLANK_SPACES}', end='\r' if team != teams[-1] else None)
        rtn = RtnSingleTeamYear(year=year, team_name=team, session=session)
        res = rtn.get_individual_scores(method=method, force_update=force_update if i == 0 else False)
        if verbose and len(res) == 0:
            print(f'\tNo scores found for {team}')
        all_scores.append(res)

    return pd.concat(all_scores)[SCHEDULE_COLS + IND_RESULTS_COLS]


def individual_nqs(year, teams, verbose=False, force_update=False):
    teams = validate_input(teams)
    session = get_session()
    
    all_nqs = []
    for i, team in enumerate(teams):
        if verbose:
            print(f'Getting individual NQS for {team}{BLANK_SPACES}', end='\r' if team != teams[-1] else None)
        rtn = RtnSingleTeamYear(year=year, team_name=team, session=session)
        res = rtn.get_individual_nqs(force_update=force_update if i == 0 else False)
        if verbose and len(res) == 0:
            print(f'\tNo individual NQS found for {team}')
        all_nqs.append(res)

    return pd.concat(all_nqs)[ROSTER_COLS + EVENTS] # + ['AA']]


def rankings(year, team_vs_ind='team', event='AA', week=None, force_update=False):
    session = get_session()
    rtn = RtnSingleTeamYear(year=year, team_name=None, session=session)
    return rtn.get_overall_rankings(team_vs_ind=team_vs_ind, event=event, week=week, force_update=force_update)
