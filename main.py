import streamlit as st
import pandas as pd
import mysql.connector
from datetime import datetime
import io
import time


conn = mysql.connector.connect(
  host="mysql20-farm1.kinghost.net",
  user="afr0202_add1",
  password="La12345",
  database="afr02", 
  port=3306
)

print(conn)

mycursor = conn.cursor()

df = pd.read_sql_query("SELECT * FROM `ocorrencia`", conn).set_index('id').drop(columns=["atualizado_em"])
df_revisados = pd.read_sql_query("SELECT * FROM `pront_revisados`", conn).set_index('id')
df_prontuarios_corretos = pd.read_sql_query("SELECT * FROM `prontuarios_corretos`", conn).set_index('id')

mes_choices = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']

st.title("Gerenciamento do prontuário")

tab1, tab2, tab3 = st.tabs(["Progresso", "Inserir Ocorrencia", "Histórico de ocorrências"])

def listar_ocorrencias(row, occ_cols):
    lista = []
    for c in occ_cols:
        if row[c] > 0:
            lista.append(f"{c} ({int(row[c])})")
    return ", ".join(lista)

with tab1:
    
    col1, col2 = st.columns([1,1])

    with col1:  
        mes_filter = st.selectbox("Mês: ", options=mes_choices, index=datetime.today().month-1, key="mes_filter")
        mes_atual = mes_choices.index(mes_filter) + 1
    with col2:
        checkbox_mes = st.checkbox("Filtrar por mes?", key="checkbox_mes")
    

    col3, col4 = st.columns([1,1])

    with col3:  
        data_filter = st.date_input("Data: ", value=datetime.today(), key="data_filter", format="DD/MM/YYYY")
    with col4:
        checkbox_data = st.checkbox("Filtrar por data?", key="checkbox_data")
    

    if checkbox_data:
        df = df[df["data"] == pd.to_datetime(data_filter).date()].copy()

    # 1) revisões do mês (sempre existem ou você vê logo)
    if checkbox_mes:
        df_rev_mes = df_revisados[df_revisados["mes"] == mes_choices[mes_atual - 1]].copy()
    else:
        df_rev_mes = df_revisados.copy()
    
    
    col5, col6, col7 = st.columns([3,3,3])

    with col5:
        data_inicial = st.date_input(
            "Data inicial:",
            value=datetime.today().date(),
            key="data_inicial",
            format="DD/MM/YYYY"
        )

    with col6:
        data_final = st.date_input(
            "Data final:",
            value=datetime.today().date(),
            key="data_final",
            format="DD/MM/YYYY"
        )

    with col7:
        checkbox_intervalo = st.checkbox("Filtrar por período?", key="checkbox_intervalo")
    
    if checkbox_intervalo:
        df["data"] = pd.to_datetime(df["data"]).dt.date

        df = df[
            (df["data"] >= data_inicial) &
            (df["data"] <= data_final)
        ].copy()
    
    
    # 2) ocorrências dessas revisões
    df_ocor_mes = df[df["revisao_id"].isin(df_rev_mes.index)].copy()
    st.write("Qtd ocorrências:", len(df_ocor_mes))

    qtd_pron_rev = len(df_revisados['prontuario'].unique())
    st.write("Qtd prontuários com pendência:", qtd_pron_rev)

    qtd_pront_corretos = df_prontuarios_corretos['prontuarios_corretos'].sum()
    st.write("Qtd prontuários corretos:", qtd_pront_corretos)
    
    st.write("Qtd prontuários analisados:", qtd_pron_rev + qtd_pront_corretos)


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


    df_por_prontuario["total_ocorrencias"] = df_por_prontuario[colunas_occ_com_uso].sum(axis=1)
    df_por_prontuario = df_por_prontuario.sort_values("total_ocorrencias", ascending=False)


    df_por_prontuario["ocorrencias"] = df_por_prontuario.apply(
    lambda r: listar_ocorrencias(r, occ_cols),
    axis=1
    )

    df_final = df_por_prontuario[
        ["prontuario", "setor", "turno", "profissional", "ocorrencias", "total_ocorrencias"]
    ]
    
    df_final = df_final[df_final["total_ocorrencias"] > 0]


    st.dataframe(df_final, use_container_width=True)


    # -------------------------
    # TABELA 2) Somatório total do mês (por tipo + total geral)
    # -------------------------
    # soma por turno
    # 1) soma por turno
    df_turno = (
        df_join
        .groupby("turno")[occ_cols]
        .sum()
    )

    # 2) coloca ocorrências nas linhas
    df_turno = df_turno.T

    # 3) normaliza nomes de turno e garante colunas fixas
    for col in ["Manhã", "Tarde"]:
        if col not in df_turno.columns:
            df_turno[col] = 0

    # 4) total
    df_turno["total"] = df_turno["Manhã"] + df_turno["Tarde"]

    # 5) voltar para formato final
    df_turno = df_turno.reset_index().rename(columns={"index": "ocorrencia"})

    df_turno = df_turno[["ocorrencia", "Manhã", "Tarde", "total"]]

    # opcional: mostrar só o que teve ocorrência
    df_turno = df_turno[df_turno["total"] > 0].sort_values("total", ascending=False)

    st.subheader("Ocorrências no mês por turno")
    st.dataframe(df_turno, use_container_width=True)

    # -------------------------
    # TABELA 3) Somatório total do mês (por tipo + total geral)
    # -------------------------
    # soma por turno
    # 1) soma por turno
    # somar ocorrências totais por linha
    df_join["total_ocorrencias"] = df_join[occ_cols].sum(axis=1)

    # agrupar por setor e turno
    df_setor = (
        df_join
        .groupby(["setor", "turno"])["total_ocorrencias"]
        .sum()
        .unstack(fill_value=0)
    )



    # garantir colunas
    for col in ["Manhã","Tarde"]:
        if col not in df_setor.columns:
            df_setor[col] = 0

    # total
    df_setor["total"] = df_setor["Manhã"] + df_setor["Tarde"]

    df_setor = df_setor.reset_index()

    st.subheader("Ocorrências no mês por setor")
    st.dataframe(df_setor[["setor","Manhã","Tarde","total"]], use_container_width=True)
    
    
    df_turno = (
        df_join
        .groupby("turno")["total_ocorrencias"]
        .sum()
        .reset_index()
    )

    st.dataframe(df_turno, use_container_width=True)



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

    mes_choices_input = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']

    mes = st.selectbox("Mês: ", options=mes_choices_input, index=datetime.today().month-1, key="mes_input")

    revisar_input = st.checkbox("Revisar prontuário?", key="revisar_input")

    if not revisar_input:
        corretos = st.number_input("Prontuários corretos: ", value=0)
    else:
        prontuario = st.number_input("Prontuário: ", value=0)


        setor_choices = [
            'Departamento Médico',    'Eletro',    'Fisioterapia Dermatofuncional',    'Fisioterapia Geral',    'Fisioterapia Motora',
            'Fisioterapia NI',    'Fisioterapia Pélvica',    'Fisioterapia Vestibular',    'Fonoaudiologia',    'Fonoaudiologia NI',
            'Fonoaudiologia TI',    'Massagem',    'Neuropsicopedagogia',    'Oficina Ortopédica',    'Pilates',    'Psicologia',
            'Psicologia NI',    'Psicologia TI',    'Psicomotricidade',    'Reintegrar',    'Respiratória',    'RPG',    'Serviço Social',
            'Terapia Ocupacional',    'Terapia Ocupacional TI'
            ]


        setor = st.selectbox("Setor: ", options=setor_choices)

        turno_choices = ["Manhã", "Tarde"]

        turno = st.selectbox("Turno: ", options=turno_choices)


        # profissional_choices = ["Neliza", "Lucas"]
        # profissional = st.selectbox("Profissional: ", options=profissional_choices)
        
        profissional = st.text_input("Profissional: ", value="")



        #===================== TABELAS OCORRENCIAS ===========================

        anex_aval_evol_entrada = st.number_input("Anexar Avaliação ou Evolução de Entrada: ", value=0)

        abrir_pront = st.number_input("Abrir prontuário: ", value=0)

        at_diaria = st.number_input("Atividade Diária: ", value=0)

        carimbar_assinar = st.number_input("Carimbar e assinar: ", value=0)

        dados_errados = st.number_input("Dados errados: ", value=0)

        datar = st.number_input("Datar: ", value=0)

        evolucao = st.number_input("Evolução: ", value=0)

        evol_alta = st.number_input("Evolução de alta: ", value=0)

        folha_enc = st.number_input("Folha de encaminhamento: ", value=0)

        info_cid = st.number_input("Informação de CID: ", value=0)

        ordem_cron = st.number_input("Ordem cronológica: ", value=0)

        preenche_campos = st.number_input("Prenchimento de todos os campos: ", value=0)

        qu_horario = st.number_input("Quadro de Horário: ", value=0)

        rasura = st.number_input("Rasura: ", value=0)

        data = st.date_input("Data: ", value=datetime.today(), format="DD/MM/YYYY", key="data_input")

        
        total_ocorrencias = evolucao + at_diaria + qu_horario + anex_aval_evol_entrada + carimbar_assinar + preenche_campos + rasura + evol_alta + datar + folha_enc + dados_errados + info_cid + ordem_cron + abrir_pront

        print(f"TOTAL OCORRÊNCIAS = {total_ocorrencias}")
    
    if st.button("Cadastrar"):
        
        if revisar_input:
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

            st.success("Ocorrências inserida com sucesso.")

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
                    data,
                    revisao_id
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, LAST_INSERT_ID())
                """
            
            val = (evolucao, at_diaria, qu_horario, anex_aval_evol_entrada, carimbar_assinar, preenche_campos, rasura, evol_alta, datar, folha_enc, dados_errados, info_cid, ordem_cron, abrir_pront, data)
            
            mycursor.execute(sql, val)

            conn.commit()

            st.success("Revisão de Prontuários inseridas com sucesso.")
            time.sleep(2)
            
            st.session_state.msg = "Atualizado prontuarios revisados com sucesso."
            st.rerun()

        else:
            sql = """
            INSERT INTO prontuarios_corretos(
                prontuarios_corretos,
                mes
            ) 
            VALUES (%s, %s)
            """
            val = (corretos, mes)
                
            mycursor.execute(sql, val)
            conn.commit()
            
            
            st.success("Prontuários corretos inserida com sucesso.")

            time.sleep(2)
            
            st.session_state.msg = "Atualizado prontuarios corretos com sucesso."
            st.rerun()
            

with tab3:
    
    df = pd.read_sql_query("SELECT * FROM `ocorrencia`", conn).set_index('id')

    
    
    df_join = df.merge(
        df_revisados,
        left_on="revisao_id",
        right_index=True,
        how="left"
    )

    mes_filter_hist = st.selectbox("Mês: ", options=mes_choices, index=datetime.today().month-1, key="mes_filter_hist")
    mes_atual_hist = mes_choices.index(mes_filter_hist)
    print(f"mes_filter_hist = {mes_filter_hist}")

    # dataframe filtrado
    df_rev_mes = df_join[df_join["mes"] == mes_choices[mes_atual_hist]].copy()

    # coluna de seleção
    df_rev_mes["Selecionar"] = False

    # editor com checkbox
    
    df_rev_mes = df_rev_mes[["Selecionar", "data", "prontuario", "setor", "turno", "profissional", "atualizado_em", "evolucao", "at_diaria", "qu_horario", "anex_aval_evol_entrada", "carimbar_assinar", "preenche_campos", "rasura", "evol_alta", "datar", "folha_enc", "dados_errados", "info_cid", "ordem_cron", "abrir_pront", "revisao_id"]]
    
    edited_df = st.data_editor(
        df_rev_mes,
        use_container_width=True,
        num_rows="fixed"
    )

    if st.button("🗑️ Apagar registros de prontuários revisados selecionados"):
        selecionados = edited_df[edited_df["Selecionar"]]

        if not selecionados.empty:
            ids_ocorrencia = selecionados.index.tolist()

            # pega os revisao_id ligados às ocorrências selecionadas
            revisoes_afetadas = selecionados["revisao_id"].dropna().unique().tolist()

            # 1) apaga as ocorrências selecionadas
            for id_oc in ids_ocorrencia:
                mycursor.execute(
                    "DELETE FROM ocorrencia WHERE id = %s",
                    (id_oc,)
                )

            # 2) para cada revisão afetada, verifica se ainda sobrou alguma ocorrência
            pronts_apagados = 0

            for revisao_id in revisoes_afetadas:
                mycursor.execute(
                    "SELECT COUNT(*) FROM ocorrencia WHERE revisao_id = %s",
                    (revisao_id,)
                )
                qtd_restante = mycursor.fetchone()[0]

                # se não restou nenhuma ocorrência, apaga o registro em pront_revisados
                if qtd_restante == 0:
                    mycursor.execute(
                        "DELETE FROM pront_revisados WHERE id = %s",
                        (revisao_id,)
                    )
                    pronts_apagados += 1

            conn.commit()

            st.success(
                f"{len(ids_ocorrencia)} ocorrência(s) apagada(s) e "
                f"{pronts_apagados} registro(s) de pront_revisados removido(s)."
            )
            
            time.sleep(2)
            st.rerun()

        else:
            st.warning("Nenhum registro selecionado.")

    
    df_pront_corr = df_prontuarios_corretos[df_prontuarios_corretos["mes"] == mes_choices[mes_atual_hist]].copy()

    # coluna de seleção
    df_pront_corr["Selecionar"] = False

    df_pront_corr = df_pront_corr[["Selecionar", "prontuarios_corretos", "atualizado_em", "mes"]]
    # editor com checkbox
    edited_df_pront_corr = st.data_editor(
        df_pront_corr,
        use_container_width=True,
        num_rows="fixed"
    )

    # botão para apagar
    if st.button("🗑️ Apagar registros de prontuarios corretos selecionados"):
        selecionados = edited_df_pront_corr[edited_df_pront_corr["Selecionar"]]

        if not selecionados.empty:

            ids = selecionados.index.tolist()

            for id_reg in ids:
                mycursor.execute("DELETE FROM prontuarios_corretos WHERE id = %s", (id_reg,))

            conn.commit()

            st.success(f"{len(ids)} registros apagados.")
            time.sleep(2)
            st.rerun()

        else:
            st.warning("Nenhum registro selecionado.")