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
df_revisados = pd.read_sql_query("SELECT * FROM `pront_revisados`", conn).set_index('id')

mes_choices = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']



st.title("Gerenciamento do prontuário")


tab1, tab2 = st.tabs(["Progresso", "Inserir Ocorrencia"])


with tab1:
    
    mes_atual = pd.Timestamp.today().month

    # 1) revisões do mês (sempre existem ou você vê logo)
    df_rev_mes = df_revisados[df_revisados["mes"] == mes_choices[mes_atual - 1]].copy()

    st.write("Qtd revisões mês:", len(df_rev_mes))

    # 2) ocorrências dessas revisões
    df_ocor_mes = df[df["revisao_id"].isin(df_rev_mes.index)].copy()
    st.write("Qtd ocorrências mês:", len(df_ocor_mes))

    # 3) colunas de ocorrência
    occ_cols = [c for c in df_ocor_mes.columns if c != "revisao_id"]

    # garantir numérico
    for c in occ_cols:
        df_ocor_mes[c] = pd.to_numeric(df_ocor_mes[c], errors="coerce").fillna(0).astype(int)

    # 4) JOIN
    df_join = df_ocor_mes.merge(
        df_rev_mes,
        left_on="revisao_id",
        right_index=True,
        how="left"
    )

    # 5) agrega por prontuário (soma ocorrências)
    group_keys = ["prontuario", "setor", "turno", "profissional"]

    df_por_prontuario = (
        df_join.groupby(group_keys, dropna=False)[occ_cols]
            .sum()
            .reset_index()
    )

    # 6) se não houver nenhuma ocorrência >0 no mês, ainda mostramos os prontuários
    colunas_occ_com_uso = [c for c in occ_cols if df_por_prontuario[c].sum() > 0]

    if len(df_por_prontuario) == 0:
        st.warning("Não achei registros para o mês atual (o join/filters retornaram vazio).")
        st.dataframe(df_rev_mes[["prontuario","setor","turno","profissional"]], use_container_width=True)

    elif len(colunas_occ_com_uso) == 0:
        st.info("Nenhuma ocorrência registrada neste mês (tudo zerado). Mostrando apenas os prontuários revisados.")
        st.dataframe(df_por_prontuario[group_keys], use_container_width=True)

    else:
        df_por_prontuario["total_ocorrencias"] = df_por_prontuario[colunas_occ_com_uso].sum(axis=1)
        df_por_prontuario = df_por_prontuario.sort_values("total_ocorrencias", ascending=False)

        st.subheader("Revisões do mês atual — por prontuário")
        st.dataframe(df_por_prontuario[group_keys + colunas_occ_com_uso + ["total_ocorrencias"]], use_container_width=True)

    # -------------------------
    # TABELA 2) Somatório total do mês (por tipo + total geral)
    # -------------------------
    totais_mes = df_ocor_mes[occ_cols].sum().sort_values(ascending=False)

    df_totais_mes = totais_mes.reset_index()
    df_totais_mes.columns = ["ocorrencia", "total_no_mes"]


    st.subheader("Somatório de ocorrências no mês atual")
    st.metric("Total geral de ocorrências no mês", int(totais_mes.sum()))
    st.dataframe(df_totais_mes, use_container_width=True)

    buffer = io.BytesIO()
    df_por_prontuario.to_excel(buffer, index=False, engine="openpyxl")
    buffer.seek(0)

    st.download_button(
        label="Download",
        data=buffer,
        file_name=f"ocorrencias{datetime.today().month}-{datetime.today().year}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="download-xlsx"
    )



with tab2:

  mes = st.selectbox("Mês: ", options=mes_choices, index=datetime.today().month-1)

  corretos = st.number_input("Prontuários corretos: ", value=0)
  
  prontuario = st.number_input("Prontuário: ", value=0)


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


  profissional_choices = ["Neliza", "Lucas"]

  profissional = st.selectbox("Profissional: ", options=profissional_choices)



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
    
    sql = """
    INSERT INTO pront_revisados(
        prontuario,
        setor,
        turno,
        profissional,
        mes
    ) 
    VALUES (%s, %s, %s, %s, %s)
    """
    val = (prontuario, setor, turno, profissional, mes)
        
    mycursor.execute(sql, val)
    conn.commit()


    print(mycursor.rowcount, "record inserted.")

    st.write("Ocorências inserida com sucesso.")

    sql = """
        INSERT INTO ocorrencia (
            evolucao,
            at_diaria,
            qu_horario,
            anex_aval_evol_entrada,
            carimbar_assinar,
            preenche_campos,
            rasura,
            evol_alta,
            datar,
            folha_enc,
            dados_errados,
            info_cid,
            ordem_cron,
            abrir_pront,
            revisao_id
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, LAST_INSERT_ID())
        """
    
    val = (evolucao, at_diaria, qu_horario, anex_aval_evol_entrada, carimbar_assinar, preenche_campos, rasura, evol_alta, datar, folha_enc, dados_errados, info_cid, ordem_cron, abrir_pront)
    
    mycursor.execute(sql, val)

    conn.commit()

    st.write("Revisão de Prontuários inseridas com sucesso.")

    st.session_state.msg = "Atualizado!"
    st.rerun()



