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

    

    st.success("Fichiers chargés")

    st.write("Aperçu conversations")
    st.dataframe(conversations.head())

    st.write("Aperçu tickets")
    st.dataframe(tickets.head())
    st.write([repr(c) for c in tickets.columns])

s    t.write("Aperçu tickets cid")
    st.dataframe(tickets_cid.head())
    st.write([repr(c) for c in tickets_cid.columns])

    st.write("Aperçu hôtels")
    st.dataframe(hotels.head())

    if st.button("Lancer l'analyse"):

        result = adoption.adoption_analytics(
            conversations,
            tickets,
            tickets_cid,
            hotels
        )

        st.success("Analyse terminée")

        st.write("Analytics")
        st.dataframe(result)

        result.to_excel("Analytics_adoption.xlsx", index=False)

        with open("Analytics_adoption.xlsx", "rb") as f:
            st.download_button(
                "Télécharger les résultats",
                f,
                file_name="Analytics_adoption.xlsx"
            )
