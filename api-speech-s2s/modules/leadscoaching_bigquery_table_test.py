from leadscoaching_bigquery_table import create_table

if __name__ == "__main__":
    # table_id = "your-project.your_dataset.your_table_name"
    table_id = "speech-s2s.bancoripley.leads_coaching"
    create_table(table_id)