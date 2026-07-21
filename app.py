import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="ระบบข้อมูลเกษตรจาก API", layout="wide")
st.title("ระบบข้อมูลเกษตรจาก API (Live Agri-Data)")
st.caption("ดึงข้อมูลจริงแบบสดจากอินเทอร์เน็ต แล้วแสดงผลโต้ตอบได้")

# ดึงข้อมูลจาก API แล้ว cache ไว้ ไม่ต้องเรียกซ้ำทุกครั้งที่ผู้ใช้ขยับปุ่ม
@st.cache_data(ttl=1800)
def ดึงอากาศ(lat, lon, days):
    url = (f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
           f"&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,"
           f"relative_humidity_2m_mean,wind_speed_10m_max,shortwave_radiation_sum"
           f"&timezone=Asia/Bangkok&forecast_days={days}")
    w = pd.DataFrame(requests.get(url, timeout=30).json()["daily"])
    w.columns = ["วันที่", "สูงสุด", "ต่ำสุด", "ฝน(มม.)",
                 "ความชื้น(%)", "ลม(กม./ชม.)", "แสง(MJ/m²)"]
    return w

@st.cache_data(ttl=1800)
def ดึงระดับน้ำ(lat, lon):
    url = (f"https://flood-api.open-meteo.com/v1/flood?latitude={lat}&longitude={lon}"
           f"&daily=river_discharge&forecast_days=30")
    r = pd.DataFrame(requests.get(url, timeout=30).json()["daily"])
    r.columns = ["วันที่", "ปริมาณน้ำ(ลบ.ม./วิ)"]
    return r

@st.cache_data(ttl=86400)
def ดึงราคาเกษตร():
    URL = "https://data.go.th/api/3/action/datastore_search"
    RESOURCE_ID = "38b840af-f119-4bea-9208-66188da5cc1b"
    recs = requests.get(URL, params={"resource_id": RESOURCE_ID, "limit": 5000},
                        timeout=30).json()["result"]["records"]
    ราคา = pd.DataFrame(recs).rename(columns={"เกษตรสำคัญบึงกาฬ": "สินค้า", "ค่า": "ราคา"})
    ราคา["ราคา"] = pd.to_numeric(ราคา["ราคา"], errors="coerce")
    return ราคา

แท็บอากาศ, แท็บน้ำ, แท็บราคา = st.tabs(
    ["สภาพอากาศ", "ระดับน้ำแม่น้ำ", "ราคาสินค้าเกษตร"])

# ---------- แท็บ 1: สภาพอากาศ (Open-Meteo) ----------
with แท็บอากาศ:
    st.subheader("พยากรณ์อากาศรายวันของสวน")
    c1, c2, c3 = st.columns(3)
    lat = c1.number_input("ละติจูด", value=18.90)
    lon = c2.number_input("ลองจิจูด", value=99.01)
    วัน = c3.slider("จำนวนวันล่วงหน้า", 3, 16, 15)
    w = ดึงอากาศ(lat, lon, วัน)
    m1, m2, m3 = st.columns(3)
    m1.metric("อุณหภูมิสูงสุดพรุ่งนี้", f"{w['สูงสุด'].iloc[1]:.0f}°C")
    m2.metric("ฝนรวม (ช่วงที่ดู)", f"{w['ฝน(มม.)'].sum():.0f} มม.")
    m3.metric("ความชื้นเฉลี่ย", f"{w['ความชื้น(%)'].mean():.0f}%")
    st.line_chart(w.set_index("วันที่")[["สูงสุด", "ต่ำสุด"]])
    st.bar_chart(w.set_index("วันที่")["ฝน(มม.)"])
    with st.expander("ดูข้อมูลดิบทั้งหมด"):
        st.dataframe(w, use_container_width=True)

# ---------- แท็บ 2: ระดับน้ำแม่น้ำ (flood API) ----------
with แท็บน้ำ:
    st.subheader("ปริมาณการไหลของแม่น้ำ (เตือนภัยน้ำท่วม)")
    c1, c2 = st.columns(2)
    lat2 = c1.number_input("ละติจูด (จุดใกล้แม่น้ำ)", value=18.90, key="lat_river")
    lon2 = c2.number_input("ลองจิจูด (จุดใกล้แม่น้ำ)", value=99.01, key="lon_river")
    r = ดึงระดับน้ำ(lat2, lon2)
    st.line_chart(r.set_index("วันที่")["ปริมาณน้ำ(ลบ.ม./วิ)"])
    st.info("ยิ่งค่าสูง = น้ำในแม่น้ำยิ่งมาก/เสี่ยงท่วม (เป็นปริมาณการไหล ไม่ใช่ระดับเป็นเมตร)")
    with st.expander("ดูข้อมูลดิบทั้งหมด"):
        st.dataframe(r, use_container_width=True)

# ---------- แท็บ 3: ราคาสินค้าเกษตร (data.go.th) ----------
with แท็บราคา:
    st.subheader("ราคาสินค้าเกษตรจริง (ข้อมูลเปิดภาครัฐ)")
    ราคา = ดึงราคาเกษตร()
    ปีล่าสุด = int(ราคา["ปี"].max())
    สินค้าทั้งหมด = sorted(ราคา["สินค้า"].dropna().unique())
    ค่าเริ่ม = [s for s in ["ทุเรียนหมอนทองคละ", "เงาะโรงเรียนคละ", "ยางแผ่นดิบชั้น 3"]
               if s in สินค้าทั้งหมด]
    เลือก = st.multiselect("เลือกสินค้าที่จะดู", สินค้าทั้งหมด, default=ค่าเริ่ม)
    st.caption(f"ข้อมูลล่าสุดปี พ.ศ. {ปีล่าสุด} — สถิติทางการรายเดือน (จ.บึงกาฬ)")
    เดือนเรียง = ["ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.",
                 "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."]
    if เลือก:
        ปีนี้ = ราคา[(ราคา["ปี"] == ปีล่าสุด) & (ราคา["สินค้า"].isin(เลือก))].copy()
        ปีนี้["เดือน"] = pd.Categorical(ปีนี้["เดือน"], categories=เดือนเรียง, ordered=True)
        ตาราง = ปีนี้.pivot_table(index="เดือน", columns="สินค้า",
                                 values="ราคา", observed=False)
        st.line_chart(ตาราง)
        เดือนล่าสุด = ตาราง.dropna(how="all").index[-1]
        st.write(f"ราคาเดือนล่าสุด ({เดือนล่าสุด} {ปีล่าสุด}) หน่วย บาท/กก.")
        st.dataframe(ตาราง.loc[[เดือนล่าสุด]].T.rename(columns={เดือนล่าสุด: "ราคา"}),
                     use_container_width=True)
    else:
        st.warning("เลือกสินค้าอย่างน้อย 1 อย่าง")
