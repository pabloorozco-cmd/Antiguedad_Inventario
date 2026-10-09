"""Sistema visual ARGOS: Pantone 382 C (lima), 2768 C (marino) y blanco."""

import streamlit as st


CSS = r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Manrope:wght@400;500;600;700;800&display=swap');
:root { --navy:#071D49; --navy-soft:#122B59; --lime:#C4D600; --white:#fff; --muted:#6B7791; --surface:#F7F9FC; --border:#E6EAF1; }
html, body, [class*="css"], [data-testid="stAppViewContainer"] { font-family: 'DM Sans', 'Segoe UI', sans-serif; }
[data-testid="stAppViewContainer"] { background:radial-gradient(ellipse 56% 35% at 93% 0%, rgba(196,214,0,.13), transparent 80%),radial-gradient(ellipse 39% 40% at 3% 65%, rgba(10,48,105,.035),transparent 70%),#F7F9FC; }
[data-testid="stHeader"] { background:transparent; }
[data-testid="stDecoration"] { display:none; }
[data-testid="stMainBlockContainer"] { max-width:1220px; padding-top:2rem; padding-bottom:4rem; }
#MainMenu, footer { visibility:hidden; }
h1,h2,h3,h4,h5 { font-family:'Manrope', 'Segoe UI', sans-serif; letter-spacing:-.035em; color:#071D49; }
p { color:#344360; }
.stButton>button, [data-testid="stFormSubmitButton"]>button { background:#C4D600!important; color:#071D49!important; border:0!important; border-radius:14px!important; font-weight:800!important; min-height:49px!important; box-shadow:0 8px 20px rgba(113,128,4,.12); transition:all .18s ease!important; }
.stButton>button:hover, [data-testid="stFormSubmitButton"]>button:hover { background:#D6EB00!important; transform:translateY(-1px); box-shadow:0 12px 22px rgba(113,128,4,.18)!important; }
.stButton>button[kind="secondary"] { background:white!important; border:1px solid #E4E9F1!important; color:#071D49!important; box-shadow:none!important; }
.stButton>button[kind="secondary"]:hover { background:#F4F6FA!important; }
[data-testid="stTextInput"] input,[data-testid="stNumberInput"] input,[data-testid="stDateInput"] input,[data-testid="stSelectbox"]>div>div { background:#FFF!important; color:#071D49!important; border-radius:12px!important; border-color:#E0E6EF!important; min-height:47px; }
[data-testid="stWidgetLabel"] p, [data-testid="stWidgetLabel"] { color:#071D49!important; font-weight:700!important; }
[data-testid="stVerticalBlockBorderWrapper"] { border-radius:19px; }
[data-testid="stAlert"] { border-radius:13px; }
[data-testid="stDataFrame"] { border-radius:12px; overflow:hidden; }
[data-testid="stSidebar"] { background:#071D49; }
[data-testid="stSidebar"] *, [data-testid="stSidebar"] p { color:#FFF; }
[data-testid="stSidebar"] [data-testid="stButton"] button { background:rgba(255,255,255,.10)!important; color:#FFF!important; border:1px solid rgba(255,255,255,.20)!important; }
[data-testid="stSidebar"] [data-testid="stButton"] button:hover { background:rgba(255,255,255,.17)!important; }
[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] svg { color:#FFF; }
.brand-row { display:flex; align-items:center; justify-content:space-between; gap:12px; margin:0 0 22px; }
.brand-left { display:flex; align-items:center; gap:13px; }
.brand-emblem { width:45px; height:45px; border-radius:13px; background:#071D49; display:flex; align-items:center; justify-content:center; box-shadow:0 9px 20px rgba(7,29,73,.16); }
.brand-emblem svg { width:30px; height:30px; }
.brand-word { font:800 21px/1 'Manrope','Segoe UI',sans-serif; letter-spacing:.16em; color:#071D49; }
.brand-desc { font-size:10px; text-transform:uppercase; color:#7A8599; font-weight:800; letter-spacing:.19em; margin-top:5px; }
.brand-chip { display:inline-flex; align-items:center; gap:8px; border:1px solid #E1E7EB; border-radius:100px; color:#486079; background:rgba(255,255,255,.86); font-size:11px; font-weight:800; text-transform:uppercase; letter-spacing:.095em; padding:10px 14px; white-space:nowrap; }
.chip-dot { display:inline-block; background:#C4D600; height:8px; width:8px; border-radius:50%; }
.hero { background:linear-gradient(126deg, #071D49 0%, #092755 56%, #102F5E 100%); min-height:385px; border-radius:26px; padding:36px 37px 30px; color:#FFF; overflow:hidden; position:relative; box-shadow:0 24px 42px rgba(7,29,73,.16); }
.hero:before { content:''; position:absolute; width:290px; height:290px; border:65px solid rgba(196,214,0,.10); border-radius:50%; right:-160px; top:-115px; }
.hero:after { content:''; position:absolute; width:210px; height:210px; border:1px solid rgba(196,214,0,.28); border-radius:50%; right:6px; top:140px; }
.hero-kicker { position:relative; font-size:11px; text-transform:uppercase; font-weight:800; letter-spacing:.19em; color:#C4D600; margin-bottom:28px; }
.hero-title { position:relative; font:800 clamp(31px,3vw,45px)/1.16 'Manrope',sans-serif; letter-spacing:-.052em; max-width:450px; color:#FFF; }
.hero-title em { color:#C4D600; font-style:normal; }
.hero-sub { position:relative; font-size:14px; line-height:1.75; color:#C7D3E4; max-width:420px; margin-top:20px; }
.hero-footer { position:relative; display:flex; gap:14px; flex-wrap:wrap; margin-top:39px; }
.hero-stat { color:#DFE9F4; font-size:11px; font-weight:700; border:1px solid rgba(255,255,255,.16); border-radius:40px; padding:9px 11px; }
.login-head { margin:6px 0 18px; }
.kicker { font-size:11px; font-weight:800; letter-spacing:.15em; text-transform:uppercase; color:#728098; }
.heading { font:800 27px/1.2 'Manrope',sans-serif; letter-spacing:-.04em; color:#071D49; margin-top:8px; }
.description { color:#79869B; font-size:13px; line-height:1.55; margin-top:8px; }
.section-title { font:800 24px/1.2 'Manrope',sans-serif; letter-spacing:-.043em; margin:12px 0 8px; color:#071D49; }
.section-sub { font-size:13px; color:#7A8798; margin:0 0 17px; }
.welcome { background:linear-gradient(120deg, #071D49, #0C2C59); color:#FFF; border-radius:23px; padding:27px 30px; min-height:152px; overflow:hidden; position:relative; }
.welcome:after { content:''; height:230px; width:230px; border:36px solid rgba(196,214,0,.11); border-radius:50%; position:absolute; right:-70px; top:-110px; }
.welcome small { color:#C4D600; font-weight:800; letter-spacing:.15em; font-size:10px; text-transform:uppercase; }
.welcome h2 { color:#FFF; font:800 27px/1.2 'Manrope',sans-serif; margin:12px 0; position:relative; }
.welcome p { color:#CDDAE9; font-size:13px; margin:0; position:relative; }
.dash-card { border:1px solid #E6EBF1; background:white; border-radius:17px; padding:clamp(20px,1.45vw,29px); box-shadow:0 10px 25px rgba(31,48,74,.035); min-height:157px; display:flex; flex-direction:column; justify-content:center; gap:7px; }
.dash-label { color:#344B68; font-weight:850; font-size:clamp(15px,1.03vw,21px); line-height:1.32; text-transform:uppercase; letter-spacing:.045em; }
.dash-value { color:#071D49; font:800 clamp(34px,2.2vw,47px)/1.13 'Manrope',sans-serif; letter-spacing:-.035em; margin-top:5px; font-variant-numeric:tabular-nums; }
.dash-helper { font-size:clamp(14px,.9vw,19px); color:#50637D; line-height:1.42; margin-top:1px; font-weight:550; }
.form-note { border:1px solid #E4E9F0; background:#FFF; border-radius:16px; padding:15px 17px; display:flex; align-items:center; gap:12px; font-size:12px; line-height:1.5; color:#607087; }
.note-icon { border-radius:10px; width:35px; height:35px; flex-shrink:0; background:#EFF4D4; color:#071D49; display:flex; align-items:center; justify-content:center; font-weight:800; }
.product-chip {display:inline-block; padding:6px 12px; border-radius:7px; font-size:10px; font-weight:900; letter-spacing:.04em; }
.status-ok { background:#ECF9E8; color:#2B7730; border:1px solid #D6EDD0; border-radius:16px; padding:16px 19px; font-weight:800; margin-top:15px; }
.empty-state { padding:30px; text-align:center; background:#FFF; border:1px dashed #DCE2EB; border-radius:18px; color:#7A869B; font-size:13px; }
.footer-mini { margin:30px 0 0; text-align:center; font-size:11px; letter-spacing:.06em; color:#91A0B2; }
.side-logo { color:#C4D600!important; font:800 23px 'Manrope',sans-serif; letter-spacing:.19em; margin:13px 0 22px; }
.side-card { border:1px solid rgba(255,255,255,.16); background:rgba(255,255,255,.06); padding:15px; border-radius:13px; }
.side-k {font-size:10px;color:#C4D600;font-weight:800;letter-spacing:.1em;text-transform:uppercase;}
.side-v {font-size:13px;color:#FFF;margin:5px 0 15px;font-weight:600;line-height:1.6;}
@media(max-width:850px) {
  [data-testid="stMainBlockContainer"] { padding:1.2rem 1rem 3rem; }
  .hero {min-height:285px; padding:27px 24px;}
  .hero-title {font-size:31px;}
  .brand-chip {display:none;}
  .welcome {padding:23px;}
}


/* Presentación adaptable de 320 px a pantallas de gran formato. */
[data-testid="stMainBlockContainer"] { width:100%; max-width: min(96vw, 1820px); padding-left:clamp(1rem,3.2vw,3rem); padding-right:clamp(1rem,3.2vw,3rem); }
[data-testid="stHorizontalBlock"] > [data-testid="stColumn"] { min-width:0; }
.brand-row,.brand-left,.hero-footer { flex-wrap:wrap; }
.brand-word { font-size:clamp(18px,1.7vw,25px); }
.brand-chip { max-width:100%; white-space:normal; }
.hero-title { font-size:clamp(30px,3.1vw,59px); }
.welcome h2 { font-size:clamp(25px,2.4vw,37px); }
.section-title { font-size:clamp(23px,2vw,32px); }
.hero,.welcome,.dash-card,.form-note { overflow-wrap:anywhere; }
.supervisor-access { border-radius:13px; border:1px solid #E1E8EE; padding:15px 18px; background:white; margin:7px 0 14px; color:#071D49; font-size:13px; }
.supervisor-access small { color:#687893; font-size:12px; }
.supervisor-welcome { min-height:145px; }

/* Semáforo ejecutivo: tabla de alto contraste en TV/desktop. */
.inv-report-scroll { overflow-x:auto; border-radius:16px; border:1px solid #DCE4EF; background:white; box-shadow:0 14px 34px rgba(7,29,73,.07); }
.inv-report { width:100%; border-collapse:separate; border-spacing:0; text-align:right; font-size:clamp(12px,.96vw,15px); color:#071D49; }
.inv-report th,.inv-report td { padding:clamp(12px,1.25vw,19px) 11px; border-right:1px solid #DFE5EF; border-bottom:1px solid #E9ECF1; }
.inv-report thead th { font-size:clamp(11px,1.06vw,16px); font-weight:800; text-align:center; white-space:nowrap; background:#C4D600; }
.inv-report thead th span { font-size:clamp(10px,.8vw,13px); white-space:nowrap; }
.inv-report thead .th-verde { background:#73AE65; color:#071D49; }
.inv-report thead .th-amarillo { background:#FFE087; color:#071D49; }
.inv-report thead .th-naranja { background:#F5AB7D; color:#071D49; }
.inv-report thead .th-rojo { background:#DE2B30; color:white; }
.inv-report tbody td:nth-child(1), .inv-report tbody td:nth-child(2) { text-align:left; font-weight:750; }
.inv-report tbody tr:hover { background:#F7F9FD; }
.inv-report td.band-verde { background:rgba(115,174,101,.07); }
.inv-report td.band-amarillo { background:rgba(255,224,135,.12); }
.inv-report td.band-naranja { background:rgba(245,171,125,.11); }
.inv-report td.band-rojo { background:rgba(222,43,48,.055); }
.inv-report td.total-cell,.inv-report td.count-cell { font-weight:800; }
.inv-report tr.inv-grand-total > * { background:#071D49!important; color:white!important; font-weight:850; text-align:right; border-color:#253C65; }
.inv-report tr.inv-grand-total th { text-align:left; }
.inv-report-mobile { display:none; }

@media(min-width:1800px) {
  [data-testid="stMainBlockContainer"] { max-width:2020px; padding-top:2.5rem; }
  .hero { min-height:440px; padding:47px; }
  .welcome { padding:38px 42px; }
  .section-sub,.welcome p { font-size:clamp(14px,.92vw,18px); }
  .dash-card { padding:clamp(24px,1.6vw,34px); }
  .dash-value { font-size:clamp(37px,2.3vw,50px); }
  .inv-report th,.inv-report td { padding-top:19px; padding-bottom:19px; }
}
@media(max-width:1050px) {
  [data-testid="stMainBlockContainer"] { max-width:100%; padding-left:1.2rem; padding-right:1.2rem; }
  .hero { min-height:315px; }
  .hero-title { font-size:clamp(30px,3.4vw,40px); }
  .inv-report { min-width:830px; }
}
@media(max-width:850px) {
  .brand-chip { display:inline-flex; }
  .inv-report-desktop { display:none; }
  .inv-report-mobile { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:12px; }
  .inv-mobile-card { border:1px solid #DFE7EF; background:white; border-radius:16px; padding:15px; min-width:0; }
  .inv-card-head { display:flex; justify-content:space-between; align-items:center; gap:10px; color:#071D49; font-size:14px; }
  .inv-card-total { color:#071D49; font:800 27px/1.2 'Manrope',sans-serif; margin:15px 0; }
  .inv-card-total span { display:block; font:500 11px/1.4 'DM Sans',sans-serif; color:#667993; margin-top:3px; }
  .mobile-bands { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:7px; }
  .mobile-band { display:flex; flex-direction:column; gap:4px; border-radius:9px; padding:9px 10px; color:#071D49; font-size:11px; }
  .mobile-band b { font-size:16px; }
  .mobile-band.band-verde { background:#E3F1D9; }
  .mobile-band.band-amarillo { background:#FFF2BE; }
  .mobile-band.band-naranja { background:#FFE5CF; }
  .mobile-band.band-rojo { background:#FFE0E0; }
  .inv-mobile-total { grid-column:1/-1; background:#071D49; border-radius:12px; padding:17px; color:white; display:flex; justify-content:space-between; align-items:center; gap:12px; }
  .inv-mobile-total span { font-size:12px; font-weight:800; }
  .inv-mobile-total strong { font:800 21px 'Manrope',sans-serif; }
}
@media(max-width:640px) {
  [data-testid="stMainBlockContainer"] { padding:1rem .85rem 2.8rem; }
  /* Las columnas de Streamlit se apilan incluso en dispositivos muy angostos. */
  [data-testid="stHorizontalBlock"] { flex-direction:column!important; align-items:stretch!important; gap:.65rem!important; }
  [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] { flex:1 1 auto!important; min-width:0!important; width:100%!important; }
  .brand-row { align-items:flex-start; gap:8px; margin-bottom:14px; }
  .brand-emblem { width:40px; height:40px; }
  .brand-word { font-size:19px; }
  .brand-desc { font-size:8.5px; letter-spacing:.11em; }
  .brand-chip { padding:7px 9px; font-size:9px; letter-spacing:.06em; }
  .hero { min-height:0; border-radius:17px; padding:23px 20px; }
  .hero-title { font-size:clamp(28px,8vw,39px); }
  .hero-kicker { margin-bottom:18px; }
  .hero-sub { font-size:12px; margin-top:15px; }
  .hero-footer { margin-top:22px; }
  .hero-stat { font-size:10px; padding:7px 9px; }
  .welcome { min-height:0; border-radius:17px; padding:22px 19px; }
  .welcome h2 { font-size:25px; }
  .welcome p { font-size:12px; }
  .section-title { font-size:23px; }
  .section-sub { font-size:12px; }
  .dash-card { min-height:145px; padding:19px 18px; gap:7px; }
  .dash-label { font-size:15px; line-height:1.3; }
  .dash-value { font-size:clamp(32px,8vw,41px); }
  .dash-helper { font-size:14px; line-height:1.45; }
  .form-note { padding:12px; align-items:flex-start; }
  .inv-report-mobile { grid-template-columns:minmax(0,1fr); gap:10px; }
  .inv-mobile-total { flex-wrap:wrap; }
  [data-testid="stDataFrame"] { max-width:100%; }
}
@media(max-width:365px) {
  .brand-chip { font-size:8px; }
  .brand-left { gap:8px; }
  .brand-word { font-size:17px; }
  .inv-mobile-card { padding:12px; }
  .mobile-band { padding:8px; }
}

/* Botón de cierre de sesión: rojo de acción y alto contraste.
   Selección por key para NO modificar otros botones verdes ARGOS. */
[class*="st-key-top_exit_supervisor"] button,
[class*="st-key-top_exit_operator"] button {
  background:#B72E3A!important;
  color:#FFFFFF!important;
  border:2px solid #B72E3A!important;
  box-shadow:0 8px 22px rgba(183,46,58,.23)!important;
  border-radius:12px!important;
  min-height:60px!important;
  font-size:clamp(20px,1.25vw,25px)!important;
  font-weight:900!important;
  letter-spacing:.055em;
  text-transform:uppercase!important;
}
/* Streamlit dibuja el texto del botón dentro de elementos <p>/<span>.
   Se fuerzan esos elementos a blanco para que no hereden el color oscuro global. */
[class*="st-key-top_exit_supervisor"] button :is(p, span),
[class*="st-key-top_exit_operator"] button :is(p, span) {
  color:#FFFFFF!important;
  -webkit-text-fill-color:#FFFFFF!important;
  font-size:clamp(20px,1.25vw,25px)!important;
  font-weight:900!important;
  line-height:1.15!important;
  letter-spacing:.055em!important;
  text-transform:uppercase!important;
}
[class*="st-key-top_exit_supervisor"] button:hover,
[class*="st-key-top_exit_operator"] button:hover {
  background:#94212C!important;
  border-color:#94212C!important;
  color:#FFFFFF!important;
  box-shadow:0 11px 24px rgba(148,33,44,.28)!important;
}
[class*="st-key-top_exit_supervisor"] button:focus-visible,
[class*="st-key-top_exit_operator"] button:focus-visible {
  outline:3px solid #071D49!important;
  outline-offset:3px!important;
}
/* Evita que la segunda celda del pie herede la alineación izquierda
   reservada a BODEGA y PRODUCTO en las filas ordinarias. */
.inv-report tbody tr.inv-grand-total td {
  text-align:right!important;
  font-variant-numeric:tabular-nums;
}

/* Supervisor: tabla de diez columnas legible en monitores, televisores y tablets. */
.inv-report-scroll { overflow-x:auto; -webkit-overflow-scrolling:touch; scrollbar-width:thin; }
.inv-report {
  table-layout:fixed;
  width:100%; min-width:1210px;
  font-size:clamp(15px,1vw,20px);
  font-variant-numeric:tabular-nums;
  line-height:1.32;
}
.inv-report col.col-depot { width:12%; }
.inv-report col.col-product { width:10%; }
.inv-report col.col-band { width:9%; }
.inv-report col.col-sacks { width:11%; }
.inv-report col.col-tonnes { width:10%; }
.inv-report col.col-orders { width:10%; }
.inv-report col.col-orders-tonnes { width:11%; }
.inv-report th,.inv-report td {
  padding:clamp(13px,.95vw,20px) clamp(7px,.6vw,13px);
  vertical-align:middle;
  overflow-wrap:break-word;
}
.inv-report thead th {
  font-size:clamp(14px,.95vw,19px);
  white-space:normal;
  line-height:1.3;
  letter-spacing:-.01em;
}
.inv-report thead th span { font-size:clamp(12px,.80vw,16px); white-space:normal; }
.inv-report tbody td { font-weight:650; }
.inv-report tbody td.depot-cell { font-weight:800; }
.inv-report .product-chip { font-size:clamp(12px,.83vw,16px); padding:7px 11px; max-width:100%; }
.inv-report td.total-cell,.inv-report td.tonnes-cell { font-weight:850; }
.inv-report td.odoo-cell { background:#F8FAFC; }
.inv-report tr.inv-grand-total > * { font-size:clamp(14px,.96vw,20px); }
.inv-report tr.inv-grand-total th { white-space:normal; }
.inv-card-orders {
  display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:9px;
  border-top:1px solid #E6EBF1; margin-top:13px; padding-top:12px;
  color:#64748B; font-size:12px; font-weight:800;
}
.inv-card-orders > span { min-height:35px; }
.inv-card-orders b { display:block; min-height:15px; }
@media(min-width:1800px) {
  .inv-report { font-size:clamp(18px,1.02vw,23px); }
  .inv-report thead th { font-size:clamp(17px,1vw,22px); }
  .inv-report thead th span { font-size:clamp(15px,.82vw,19px); }
}
@media (max-width:1290px) and (min-width:851px) {
  .inv-report { min-width:1210px; }
}
@media(max-width:850px) {
  .inv-card-total span { font-size:13px; }
  .inv-card-head { font-size:16px; }
  .mobile-band { font-size:13px; }
  .mobile-band b { font-size:18px; }
}


/* Bodegas agrupadas: la celda con rowspan abarca todos sus productos.
   Evita que las reglas nth-child antiguas desalineen cifras en filas sin BODEGA. */
.inv-report tbody th.depot-cell {
  vertical-align:middle!important;
  text-align:center!important;
  font-family:'Manrope','Segoe UI',sans-serif;
  font-size:clamp(16px,1.02vw,22px);
  font-weight:850;
  line-height:1.35;
  color:#071D49;
  background:#F1F5FA;
  white-space:normal;
  overflow-wrap:break-word;
  border-right:2px solid #D4DFEA;
  padding:16px 10px;
}
.inv-report tbody td.product-cell { text-align:left!important; font-weight:750; }
.inv-report tbody td.band-cell,
.inv-report tbody td.total-cell,
.inv-report tbody td.tonnes-cell,
.inv-report tbody td.odoo-cell { text-align:right!important; }
.inv-report tbody.inv-warehouse-group:not(:first-of-type) tr:first-child > * {
  border-top:2px solid #C8D4E3;
}
/* Móviles: encabezado único por bodega y fichas agrupadas debajo. */
.inv-mobile-warehouse { grid-column:1/-1; min-width:0; }
.inv-mobile-warehouse-title {
  background:#EAF0F7;
  border-left:5px solid #C4D600;
  border-radius:10px;
  padding:12px 16px;
  margin-bottom:10px;
  font:850 clamp(16px,2.5vw,21px)/1.35 'Manrope',sans-serif;
  color:#071D49;
}
.inv-mobile-products { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:12px; }
@media(max-width:640px) {
  .inv-mobile-products { grid-template-columns:minmax(0,1fr); gap:10px; }
}

</style>
"""


def apply_style() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
