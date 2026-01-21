import streamlit as st
import pandas as pd
import mysql.connector
from datetime import datetime
import io



conn = mysql.connector.connect(
  host="mysql20-farm1.kinghost.net",
  user="afr0202_add1",
  password="La12345",
  database="afr02", 
  port=3306
)

print(conn)


mycursor = conn.cursor()

df = pd.read_sql_query("SELECT * FROM `ocorrencia`", conn).set_index('id')
df_setor = pd.read_sql_query("SELECT * FROM `setor`", conn).set_index('id')
df_turno = pd.read_sql_query("SELECT * FROM `turno`", conn).set_index('id')
df_revisados = pd.read_sql_query("SELECT * FROM `pront_revisados`", conn).set_index('id')


st.title("Gerenciamento do prontuário")


tab1, tab2 = st.tabs(["Progresso", "Inserir Ocorrencia"])


with tab1:
    st.markdown("## Progresso")

    df
    df_setor
    df_turno
    df_revisados

    buffer = io.BytesIO()
    df.to_excel(buffer, index=False, engine="openpyxl")
    buffer.seek(0)

    st.download_button(
        label="Download",
        data=buffer,
        file_name=f"ocorrencias{datetime.today().month}-{datetime.today().year}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="download-xlsx"
    )



with tab2:
  mes_choices = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']

  mes = st.selectbox("Mês: ", options=mes_choices, index=datetime.today().month-1)

  corretos = st.number_input("Prontuários corretos: ", value=0)
  
  pendencia = st.number_input("Prontuários com pendência: ", value=0)


  setor_choices = ['Reintegrar', 'Eletro', 'Fisioterapia Geral', 'Fonoaudiologia',
        'Respiratória', 'Departamento Médico', 'Psicologia TI',
        'Terapia Ocupacional', 'Terapia Ocupacional TI', None,
        'Fisioterapia NI', 'Fonoaudiologia NI', 'Psicologia NI',
        'Massagem', 'Pilates', 'RPG', 'Oficina Ortopédica',
        'Neuropsicopedagogia', 'Psicologia', 'Psicomotricidade',
        'Fisioterapia Dermatofuncional', 'Fonoaudiologia TI',
        'Fisioterapia Pélvica', 'Fisioterapia Motora  ', 'Serviço Social',
        'Fisioterapia Vestibular']


  setor = st.selectbox("Setor: ", options=setor_choices)

  turno_choices = ["Manhã", "Tarde"]

  turno = st.selectbox("Turno: ", options=turno_choices)



  #===================== TABELAS OCORRENCIAS ===========================

  evolucao = st.number_input("Evolução: ", value=0)

  at_diaria = st.number_input("Atividade Diária: ", value=0)

  qu_horario = st.number_input("Quadro de Horário: ", value=0)

  anex_aval_evol_entrada = st.number_input("Anexar Avaliação ou Evolução de Entrada: ", value=0)

  carimbar_assinar = st.number_input("Carimbar e assinar: ", value=0)

  preenche_campos = st.number_input("Prenchimento de todos os campos: ", value=0)

  rasura = st.number_input("Rasura: ", value=0)

  evol_alta = st.number_input("Evolução de alta: ", value=0)

  datar  = st.number_input("Datar: ", value=0)

  folha_enc  = st.number_input("Folha de encaminhamento: ", value=0)

  dados_errados  = st.number_input("Dados errados: ", value=0)

  info_cid  = st.number_input("Informação de CID: ", value=0)

  ordem_cron  = st.number_input("Ordem cronológica: ", value=0)

  abrir_pront  = st.number_input("Abrir prontuário: ", value=0)

  
  total_ocorrencias = evolucao + at_diaria + qu_horario + anex_aval_evol_entrada + carimbar_assinar + preenche_campos + rasura + evol_alta + datar + folha_enc + dados_errados + info_cid + ordem_cron + abrir_pront

  print(f"TOTAL OCORRÊNCIAS = {total_ocorrencias}")
  
  if st.button("Cadastrar"):


      sql = "UPDATE ocorrencia SET evolucao = %s, at_diaria = %s, qu_horario = %s, anex_aval_evol_entrada = %s, carimbar_assinar = %s, preenche_campos = %s, rasura = %s, evol_alta = %s, datar = %s, folha_enc = %s, dados_errados = %s, info_cid = %s, ordem_cron = %s, abrir_pront = %s, mes = %s"
      val = (int(df['evolucao'].values[0])+evolucao, int(df['at_diaria'].values[0])+at_diaria, int(df['qu_horario'].values[0])+qu_horario, int(df['anex_aval_evol_entrada'].values[0])+anex_aval_evol_entrada, int(df['carimbar_assinar'].values[0])+carimbar_assinar, int(df['preenche_campos'].values[0])+preenche_campos, int(df['rasura'].values[0])+rasura, int(df['evol_alta'].values[0])+evol_alta, int(df['datar'].values[0])+datar, int(df['folha_enc'].values[0])+folha_enc, int(df['dados_errados'].values[0])+dados_errados, int(df['info_cid'].values[0])+info_cid, int(df['ordem_cron'].values[0])+ordem_cron, int(df['abrir_pront'].values[0])+abrir_pront,
  mes)
      mycursor.execute(sql, val)

      conn.commit()

      print(mycursor.rowcount, "record inserted.")

      st.write("Ocorências inseridas com sucesso.")

      sql = "UPDATE setor SET total = total + %s WHERE setor = %s"
      val = (total_ocorrencias, setor)
      mycursor.execute(sql, val)

      conn.commit()

      print(mycursor.rowcount, "record inserted.")

      st.write("Setor inseridas com sucesso.")


      sql = "UPDATE turno SET total = total + %s WHERE turno = %s"
      val = (total_ocorrencias, turno)
      mycursor.execute(sql, val)

      conn.commit()

      print(mycursor.rowcount, "record inserted.")

      st.write("Turno inseridas com sucesso.")

      sql = "UPDATE pront_revisados SET corretos = corretos + %s, com_pendencia = com_pendencia + %s"
      val = (corretos, pendencia)
      mycursor.execute(sql, val)

      conn.commit()

      print(mycursor.rowcount, "record inserted.")

      st.write("Revisão de Prontuários inseridas com sucesso.")

      st.session_state.msg = "Atualizado!"
      st.rerun()
      


