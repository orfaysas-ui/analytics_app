import streamlit as st
import pandas as pd
import adoption
import re


st.title("Analyse automatique")

export_conv = st.file_uploader("Export Conversations", type=["xlsx", "csv"])

export_ticket = st.file_uploader("Export Tickets (ALL)", type=["xlsx", "csv"])

export_ticket_cid = st.file_uploader("Export Tickets (With CID)", type=["xlsx", "csv"])

hotels = st.file_uploader("Hotel List", type=["xlsx", "csv"])

def read_file(file):

    if file.name.endswith(".xlsx"):
        return pd.read_excel(file)

    elif file.name.endswith(".csv"):

        for encoding in [
            "utf-8",
            "utf-8-sig",
            "cp1252",
            "latin1"
        ]:
            try:
                file.seek(0)
                return pd.read_csv(
                    file,
                    encoding=encoding
                )
            except:
                pass

        raise ValueError(
            f"Impossible de lire {file.name}"
        )
if export_conv and export_ticket and export_ticket_cid and hotels:

    conversations = read_file(export_conv)
    tickets = read_file(export_ticket)
    tickets_cid = read_file(export_ticket_cid)
    hotels = read_file(hotels)

    conv_dates = pd.to_datetime(conversations["started"].str.replace(" Europe/Paris", "", regex=False), errors="coerce").dt.tz_localize("Europe/Paris")
    ticket_dates = pd.to_datetime(tickets["Créé le"], errors="coerce")

    min_data_date = max(conv_dates.min().date(), ticket_dates.min().date())
    max_data_date = min(conv_dates.max().date(), ticket_dates.max().date())

    start_date = st.date_input(
        "Date de début d'analyse",
        value=min_data_date,
        min_value=min_data_date,
        max_value=max_data_date
    )

    end_date = st.date_input(
        "Date de fin d'analyse",
        value=max_data_date,
        min_value=min_data_date,
        max_value=max_data_date
    )

    if start_date < min_data_date:
        st.error(f"La date de début doit être au plus tôt le {min_data_date}.")
        st.stop()

    if end_date > max_data_date:
        st.error(f"La date de fin doit être au plus tard le {max_data_date}.")
        st.stop()

    if start_date > end_date:
        st.error("La date de début ne peut pas être après la date de fin.")
        st.stop()
    

    st.success("Fichiers chargés")

    st.write("Aperçu conversations")
    st.dataframe(conversations.head())

    st.write("Aperçu tickets")
    st.dataframe(tickets.head())

    st.write("Aperçu tickets cid")
    st.dataframe(tickets_cid.head())

    st.write("Aperçu hôtels")
    st.dataframe(hotels.head())

    if st.button("Lancer l'analyse"):

        result = adoption.adoption_analytics(
            conversations,
            tickets,
            tickets_cid,
            hotels,
            start_date,
            end_date       
        )

        st.success("Analyse terminée")

        st.write("General adoption")
        st.dataframe(result[0])

        st.write("Adoption per week")
        st.dataframe(result[1])
        

        result[0].to_excel("General_adoption.xlsx", index=False)

        with open("General_adoption.xlsx", "rb") as f:
            st.download_button(
                "Télécharger les résultats (Adoption générale)",
                f,
                file_name="General_adoption.xlsx"
            )

        result[1].to_excel("Adoption_per_week.xlsx", index=False)

        with open("Adoption_per_week.xlsx", "rb") as f:
            st.download_button(
                "Télécharger les résultats (Adoption par semaine)",
                f,
                file_name="Adoption_per_week.xlsx"
            )
