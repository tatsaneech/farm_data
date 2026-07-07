import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="ระบบข้อมูลสวนลำไย", layout="wide")
st.title("ระบบข้อมูลสวนลำไย (Farm Data Platform)")

แท็บอากาศ, แท็บน้ำ, แท็บสำรวจ, แท็บสะอาด = st.tabs(
    ["สภาพอากาศ", "ระดับน้ำแม่น้ำ", "สำรวจข้อมูล", "ทำความสะอาด"])

# ---------- แท็บ 1: สภาพอากาศจาก API ----------
with แท็บอากาศ:
    st.subheader("พยากรณ์อากาศ 15 วัน (Open-Meteo)")
    lat = st.number_input("ละติจูด", value=18.90)
    lon = st.number_input("ลองจิจูด", value=99.01)
    if st.button("ดึงอากาศ 15 วัน"):
        url = (f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
               f"&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,"
               f"relative_humidity_2m_mean,wind_speed_10m_max,shortwave_radiation_sum"
               f"&timezone=Asia/Bangkok&forecast_days=15")
        d = requests.get(url).json()["daily"]
        w = pd.DataFrame(d)
        w.columns = ["วันที่", "สูงสุด", "ต่ำสุด", "ฝน(มม.)",
                     "ความชื้น(%)", "ลม(กม./ชม.)", "แสง(MJ/m²)"]
        st.dataframe(w, use_container_width=True)
        st.line_chart(w.set_index("วันที่")[["สูงสุด", "ต่ำสุด"]])
        st.bar_chart(w.set_index("วันที่")["ฝน(มม.)"])
        st.line_chart(w.set_index("วันที่")["ความชื้น(%)"])
        st.bar_chart(w.set_index("วันที่")[["ลม(กม./ชม.)", "แสง(MJ/m²)"]])

# ---------- แท็บ 2: ระดับน้ำแม่น้ำ (เตือนภัยน้ำท่วม) ----------
with แท็บน้ำ:
    st.subheader("ปริมาณน้ำในแม่น้ำ 15 วัน (Open-Meteo Flood API)")
    st.caption("ใช้พิกัดเดียวกับแท็บอากาศ — ควรอยู่ใกล้แม่น้ำจริง ค่าถึงจะมีความหมาย")
    if st.button("ดึงระดับน้ำแม่น้ำ 15 วัน"):
        url = (f"https://flood-api.open-meteo.com/v1/flood?latitude={lat}&longitude={lon}"
               f"&daily=river_discharge&forecast_days=15")
        d = requests.get(url).json()["daily"]
        r = pd.DataFrame(d)
        r.columns = ["วันที่", "ปริมาณน้ำ(ลบ.ม./วิ)"]
        st.dataframe(r, use_container_width=True)
        st.line_chart(r.set_index("วันที่")["ปริมาณน้ำ(ลบ.ม./วิ)"])
        st.info("ค่านี้คือ *ปริมาณการไหล* (ลบ.ม./วินาที) ยิ่งสูง = น้ำยิ่งมาก/เสี่ยงท่วมมากขึ้น "
                "(ไม่ใช่ระดับน้ำเป็นเมตรตรง ๆ แต่ไปทางเดียวกัน)")

# ---------- แท็บ 3: สำรวจข้อมูล ----------
with แท็บสำรวจ:
    st.subheader("อัปโหลด CSV เพื่อดูสถิติและกราฟ")
    f1 = st.file_uploader("อัปโหลด CSV ข้อมูลสวน", type="csv", key="explore")
    if f1:
        df = pd.read_csv(f1)
        st.dataframe(df, use_container_width=True)
        st.write(df.describe())
        num = df.select_dtypes("number").columns.tolist()
        if num:
            st.bar_chart(df[st.selectbox("คอลัมน์", num)])
        if len(num) >= 2:
            st.write("ความสัมพันธ์ (correlation)")
            st.write(df[num].corr())

# ---------- แท็บ 4: ทำความสะอาด ----------
with แท็บสะอาด:
    st.subheader("อัปโหลด CSV เพื่อเติมค่าว่าง/ลบค่าผิดปกติ")
    f2 = st.file_uploader("อัปโหลด CSV เพื่อทำความสะอาด", type="csv", key="clean")
    if f2:
        df = pd.read_csv(f2)
        st.write("ค่าว่างแต่ละคอลัมน์:", df.isnull().sum())
        num = df.select_dtypes("number").columns
        for c in num:
            df[c] = df[c].fillna(df[c].mean())
        if len(num) > 0:
            col = st.selectbox("คอลัมน์ลบค่าผิดปกติ (IQR)", num)
            Q1, Q3 = df[col].quantile(0.25), df[col].quantile(0.75)
            IQR = Q3 - Q1
            ก่อน = len(df)
            df = df[(df[col] >= Q1 - 1.5*IQR) & (df[col] <= Q3 + 1.5*IQR)]
            st.info(f"ลบค่าผิดปกติออก {ก่อน - len(df)} แถว")
        st.dataframe(df, use_container_width=True)
        st.download_button("ดาวน์โหลดไฟล์ที่สะอาด",
                           df.to_csv(index=False).encode("utf-8-sig"),
                           "cleaned.csv", "text/csv")
