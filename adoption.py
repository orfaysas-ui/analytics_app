import pandas as pd
import utils
import datetime
import re

def get_hotel_code(eq, tickets):
    eq = eq.copy()
    tickets = tickets.copy()
    #GET HOTEL CODE
    #get mask
    mask = (
        eq["hotelCode"].str.match(
        r"^h\d{4}$",
        flags=re.IGNORECASE,
        na=False) 
    )&(~ eq.hotelCode.isna())&(eq.hotelCode != 'HXXXX')
    #get hotel codes from transcript
    eq['hotel_code_transcript']= eq["transcript"].str.extract(r"(h\d{4})", flags=re.IGNORECASE, expand=False)
    #get hotel codes from tid
    hotel_codes_tid = eq[mask].groupby('customerHandle').agg(
         hotel_code_tid = ('hotelCode','first')
        ).reset_index().rename(columns={'hotelCode':'hotel_code_tid'})
    eq=eq.merge(hotel_codes_tid, how='left', on = 'customerHandle')
    #get final hotel code
    eq.loc[mask,'hotel_code'] = eq.hotelCode
    eq.loc[~mask,'hotel_code'] = eq.hotel_code_transcript.fillna(eq.hotel_code_tid)
    eq['hotel_code']=eq.hotel_code.str.upper()
    hc_conv = eq[['id','hotel_code']]
    tickets['hotel_code']="H" + tickets["Compte"].str.extract(r"^(.{4})", expand=False)
    hc_ticket = tickets[['Numéro','hotel_code']]
    return (hc_conv, hc_ticket)

def get_clean_dates(e,t,h):
    t = t.copy()
    h = h.copy()
    #get proper date
    t['date']=pd.to_datetime(t['Créé le'])

    dates = utils.clean_dates(e)
    h['launch_date']=pd.to_datetime(h['Launch date'],dayfirst = True)

    #nb days since launch
    today_date = pd.Timestamp.today().date()
    h['today_date']=pd.to_datetime(today_date)
    h['nb_days_since_launch']=(h.today_date-h.launch_date).dt.days
    h['nb_weeks_since_launch']=h.nb_days_since_launch//7
    dt_conv = dates[['id','date']]
    dt_tickets= t[['Numéro','date']]
    return(dt_conv,dt_tickets,h)

def remove_blank_csat (eq):
    #REMOVE BLANK CONV AND SURVEY
    transcript = utils.get_transcript(eq)
    questions = utils.get_questions(transcript)
    cgm = utils.conv_gen_metrics(questions)
    #enlever les sans questions et les csat
    tab = eq.merge(cgm, how='left',on='id')
    tab = tab[
        (tab.assignee!='csat-survey')
        &
        (tab.nb_questions>0)]
    return tab


def adoption_analytics (eq,tickets,tickets_cid,hotels):
    clean_hc = get_hotel_code(eq,tickets)
    clean_dates = get_clean_dates(eq,tickets,hotels)
    eq = eq.merge(clean_hc[0],how='left', on = 'id')
    eq = eq.merge(clean_dates[0], how='left', on = 'id')
    print(eq.date)
    tab = remove_blank_csat(eq)

    tickets = tickets.merge(clean_hc[1],how='left', on = 'Numéro')
    tickets = tickets.merge(clean_dates[1], how='left', on = 'Numéro')
    print(tickets.date)
    
    hotels = clean_dates[2]

    hotels['hotel_code']=hotels['Hotel code']

    last_date_measured = tab.date.max()
    last_day_ticket = tickets['date'].max()

    tickets= tickets.merge(hotels[['hotel_code','launch_date']], how='left', on = 'hotel_code')
    tickets = tickets[
        (tickets.date.dt.date<=last_date_measured)
        &(tickets.date.dt.date>=tickets.launch_date)
        ]
    
    tab["date"] = pd.to_datetime(tab["date"], errors="coerce").dt.tz_localize(None)
    last_day_ticket = pd.to_datetime(last_day_ticket).tz_localize(None)

    conv = tab[tab["date"] <= last_day_ticket]

    #group by conv
    hconv = conv.groupby('hotel_code').id.nunique().reset_index().rename(columns={'id':'nb_conv'})

    #groupby ticket
    tickets['through_butler']=tickets['Numéro'].isin(tickets_cid['Numéro'])

    nb_tickets_tot = tickets.groupby('hotel_code')['Numéro'].nunique().reset_index().rename(columns={'Numéro':'nb_tickets_tot'})
    nb_tickets_butler = tickets[tickets.through_butler==True].groupby('hotel_code')['Numéro'].nunique().reset_index().rename(columns={'Numéro':'nb_tickets_butler'})

    #merges
    hotel_adoption = hotels.merge(nb_tickets_tot, how='left', on='hotel_code')
    hotel_adoption = hotel_adoption.merge(nb_tickets_butler, how='left', on='hotel_code')
    hotel_adoption = hotel_adoption.merge(hconv, how='left', on = 'hotel_code')

    #new metrics
    hotel_adoption['nb_conv_per_week_since_launch']=hotel_adoption.nb_conv.fillna(0)/hotel_adoption.nb_weeks_since_launch
    hotel_adoption['tot_nb_demands']= hotel_adoption.nb_conv.fillna(0) + hotel_adoption.nb_tickets_tot.fillna(0) - hotel_adoption.nb_tickets_butler.fillna(0)
    hotel_adoption['adoption_rate']=hotel_adoption.nb_conv.fillna(0)/hotel_adoption.tot_nb_demands

    return hotel_adoption
