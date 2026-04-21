import pandas as pd
from pathlib import Path

# 获取当前文件所在目录
current_file_dir = Path(__file__).parent



df_E4C_Session_25 = pd.read_excel(current_file_dir/"../rawData/20240530_20250530_recharge_detail_records.xlsx")
df_E4C_Session_25 = df_E4C_Session_25.iloc[:, 1:] # 读取后删除第一列
df_DX_Session = df_E4C_Session_25[df_E4C_Session_25['location_name'] == 'PS 030-1 - IPP - Drahi - X']

#B103
path_b103_25 = current_file_dir/"../rawData/building103/sessionRepport_EN_31_12_2025_03_16_37_688.xlsx" 
path_b103_24 = current_file_dir/"../rawData/building103/sessionRepport_EN_31_12_2024_03_15_45_940.xlsx"
path_b103_23 = current_file_dir/"../rawData/building103/sessionRepport_EN_31_12_2023_03_18_23_207.xlsx"

df_b103_25 = pd.read_excel(path_b103_25, sheet_name=2)
df_b103_24 = pd.read_excel(path_b103_24, sheet_name=2)
df_b103_23 = pd.read_excel(path_b103_23, sheet_name=2)

df_merged_b103 = pd.concat([df_b103_25, df_b103_24, df_b103_23], ignore_index=True)

# clean B103
cols_to_drop = ['Unnamed: 0','idle fee','eMi3','Location','Zone','SubOperator','Evse','charge amount','CPO GROUP','organisation','EMSP','EMSP CODE','Valorization Incl. tax (EUR)','Valorization Excl. tax (EUR)','Payment type','TVA/Siren','Evse max power (kW)', 'Notification Date']
df_cleaned_b103 = df_merged_b103.drop(columns=cols_to_drop)
df_cleaned_b103['Evse Id'] = df_cleaned_b103['Evse Id'].str.extract(r'-(\d+)$')

df_cleaned_b103['plug type'] = df_cleaned_b103['plug type'].replace({
    'T2S': 'AC-Level2',
    'EF': 'AC-Level1'
})

df_cleaned_b103['compliance'] = df_cleaned_b103['compliance'].replace({
    'valid': 'ended',
    'invalid': 'failed'
})

df_cleaned_b103 = df_cleaned_b103.dropna().reset_index(drop=True)