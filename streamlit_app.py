from __future__ import annotations
import math
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title='SemiconFlow-NE | NESFIC 2026', page_icon='🧩', layout='wide', initial_sidebar_state='collapsed')

st.markdown('''<style>
.block-container{padding-top:1rem;padding-bottom:2rem;max-width:1500px}
.hero{padding:1.15rem 1.3rem;border:1px solid rgba(120,120,120,.22);border-radius:18px;margin-bottom:1rem;background:linear-gradient(120deg,rgba(80,88,170,.10),rgba(20,135,120,.08))}
.hero h1{margin:0;font-size:2.35rem;line-height:1.08}.hero p{margin:.5rem 0 0 0;font-size:1.03rem}
.badge{display:inline-block;padding:.22rem .58rem;border-radius:999px;border:1px solid rgba(120,120,120,.28);margin-right:.35rem;font-size:.78rem}
.callout{padding:.85rem 1rem;border-left:4px solid rgba(86,91,170,.68);background:rgba(120,120,120,.06);border-radius:8px}
.smallnote{font-size:.82rem;opacity:.78}
[data-testid="stMetric"]{border:1px solid rgba(120,120,120,.18);padding:.6rem .75rem;border-radius:14px;background:rgba(120,120,120,.03)}
</style>''', unsafe_allow_html=True)

@st.cache_data
def build_data():
    rng=np.random.default_rng(260928)
    tech=pd.DataFrame([
        ['WB','Wire Bond',.36],['FC','Flip Chip',.30],['ISP','Integrated Systems Packaging',.22],['ADV','Advanced Packaging (illustrative)',.12]
    ],columns=['tech_id','technology','portfolio_weight'])
    categories=[
        ('Leadframes','WB',.88,'Metal interconnect / package frame'),('Bond wire','WB',.95,'Electrical interconnect'),('Molding compound','WB',.92,'Package encapsulation'),('Die attach adhesive','WB',.85,'Die attach'),('Wafer backgrind consumables','WB',.70,'Wafer preparation'),('Dicing blades','WB',.73,'Singulation consumable'),('Test sockets','WB',.82,'Final test interface'),('JEDEC trays / reels','WB',.65,'Handling and outbound packaging'),
        ('Substrate - FC class','FC',.98,'Package substrate'),('Underfill material','FC',.90,'Reliability / gap fill'),('Solder bumps / spheres','FC',.91,'Interconnect'),('Flux chemistry','FC',.83,'Assembly chemistry'),('Thermal interface material','FC',.76,'Thermal management'),('Flip-chip tool consumables','FC',.87,'Bonding process consumable'),('Advanced test interface','FC',.89,'Final test interface'),('Moisture barrier packaging','FC',.68,'Sensitive outbound packaging'),
        ('High-density substrate','ISP',.99,'Integrated package substrate'),('Interposer / redistribution material','ISP',.97,'High-density interconnect'),('Fine-pitch attach material','ISP',.94,'Assembly material'),('Advanced molding compound','ISP',.93,'Encapsulation'),('Precision adhesives','ISP',.79,'Assembly / structural'),('Specialty cleaning chemistry','ISP',.72,'Process cleaning'),('Metrology consumables','ISP',.86,'Inspection / measurement'),('Reliability test fixtures','ISP',.84,'Qualification / reliability'),
        ('Specialty gases','ADV',.88,'Process utility / controlled atmosphere'),('High-purity chemicals','ADV',.91,'Process chemistry'),('Vacuum-system consumables','ADV',.78,'Equipment support'),('Precision filters','ADV',.74,'Process utility'),('ESD-safe packaging','ADV',.69,'Sensitive electronics logistics'),('Temperature-control packaging','ADV',.67,'Sensitive inbound logistics'),('Critical equipment spares','ADV',.96,'Maintenance / uptime'),('Probe / test cards','ADV',.95,'Electrical test'),('Calibration standards','ADV',.80,'Metrology'),('Cleanroom consumables','ADV',.71,'Controlled environment'),('Specialty carrier tapes','ADV',.64,'Outbound packaging'),('Moisture-sensitive storage media','ADV',.66,'Storage / handling')]
    mat=pd.DataFrame(categories,columns=['material','tech_id','criticality','function'])
    mat.insert(0,'material_id',[f'M{i:02d}' for i in range(1,len(mat)+1)])
    regions=['Assam / Northeast India','Eastern India','Western India','Southern India','Northern India','Taiwan','Japan','South Korea','Singapore','Malaysia','Vietnam','Thailand','China','Germany','United States','Rest of India']
    source_type=['India']*5+['External']*10+['India']
    lead_base=[6,8,12,11,10,21,24,23,18,20,19,18,22,27,29,13]
    suppliers=pd.DataFrame({'supplier_id':[f'S{i:02d}' for i in range(1,17)],'supplier':[f'Supplier {chr(64+i)}' for i in range(1,17)],'region':regions,'source_type':source_type,'lead_base':lead_base})
    rows=[]
    for _,m in mat.iterrows():
        pext=.45+.40*m.criticality
        pool=suppliers[suppliers.source_type.eq('External')] if rng.random()<pext else suppliers[suppliers.source_type.eq('India')]
        p=pool.iloc[int(rng.integers(0,len(pool)))]
        share=float(rng.uniform(.62,.88))
        rows.append([m.material_id,p.supplier_id,p.supplier,p.region,p.source_type,share,'Qualified',int(max(4,round(p.lead_base+rng.normal(0,2))))])
    pri=pd.DataFrame(rows,columns=['material_id','supplier_id','supplier','region','source_type','supplier_concentration','qualification_status','lead_time_days'])
    q=[]
    for _,m in mat.iterrows():
        daily=float(rng.uniform(45,520)*(0.7+0.6*m.criticality)); cover=float(rng.uniform(4,36)); stock=int(round(daily*cover)); cv=float(rng.uniform(.18,.52)); service=float(rng.choice([.95,.97,.98,.99],p=[.25,.35,.25,.15])); unit=float(rng.uniform(220,5500)*(0.7+m.criticality))
        q.append([m.material_id,daily,stock,cover,cv,service,unit])
    inv=pd.DataFrame(q,columns=['material_id','daily_requirement','on_hand_qty','days_cover','demand_cv','target_service','unit_cost_inr'])
    df=mat.merge(pri,on='material_id').merge(inv,on='material_id')
    df['import_dependency']=np.where(df.source_type.eq('External'),rng.uniform(.72,.98,len(df)),rng.uniform(.15,.55,len(df)))
    df['disruption_risk']=np.where(df.source_type.eq('External'),rng.uniform(.14,.29,len(df)),rng.uniform(.08,.18,len(df)))
    df['local_feasibility']=np.clip(.68-.28*df.criticality+rng.normal(0,.12,len(df))+np.where(df.material.str.contains('packaging|tray|reel|filter|adhesive|cleanroom|storage|carrier',case=False,regex=True),.18,0),.15,.92)
    df['annual_spend_proxy_inr']=df.daily_requirement*365*df.unit_cost_inr
    ln=np.log1p(df.annual_spend_proxy_inr); spend=(ln-ln.min())/(ln.max()-ln.min()); lead=(df.lead_time_days-df.lead_time_days.min())/(df.lead_time_days.max()-df.lead_time_days.min())
    df['localization_score']=100*(.30*df.criticality+.25*df.import_dependency+.15*df.supplier_concentration+.10*lead+.10*spend+.10*df.local_feasibility)
    df['localization_score']=df.localization_score.round(1)
    z=df.target_service.map({.95:1.645,.97:1.881,.98:2.054,.99:2.326})
    df['safety_stock']=(z*df.daily_requirement*df.demand_cv*np.sqrt(df.lead_time_days)).round()
    df['strategic_buffer_days']=np.clip(df.criticality*df.import_dependency*df.disruption_risk*75+df.lead_time_days*.15,2,24).round(1)
    df['recommended_buffer_qty']=(df.daily_requirement*df.strategic_buffer_days+df.safety_stock).round().astype(int)
    df['buffer_gap_qty']=np.maximum(0,df.recommended_buffer_qty-df.on_hand_qty).astype(int)
    df['risk_score']=100*(.30*df.criticality+.22*df.import_dependency+.18*df.supplier_concentration+.18*df.disruption_risk/.35+.12*np.clip(df.lead_time_days/30,0,1))
    df['risk_score']=df.risk_score.clip(0,100).round(1)
    df['risk_band']=pd.cut(df.risk_score,[-1,45,65,100],labels=['LOW','MEDIUM','HIGH']).astype(str)
    df['availability_ratio']=np.clip((df.days_cover+.25*df.strategic_buffer_days)/(.9*df.lead_time_days+6),.20,1.0)
    cap=[]
    for _,t in tech.iterrows():
        d=df[df.tech_id==t.tech_id].sort_values(['criticality','risk_score'],ascending=False)
        mr=float(d.head(max(3,int(len(d)*.55))).availability_ratio.quantile(.25)); exe=float(np.clip(.58+.42*mr,0,1)); bind=d.sort_values(['availability_ratio','criticality'],ascending=[True,False]).iloc[0]
        cap.append([t.tech_id,t.technology,1.0,exe,bind.material,1-exe])
    cap=pd.DataFrame(cap,columns=['tech_id','technology','nominal_capacity_index','executable_capacity_index','binding_input','capacity_gap'])
    # synthetic stress suite
    val=pd.DataFrame([
        ['Supplier outage - 14 days',.72,.86,16,9],['East-Asia lead-time shock',.68,.82,20,12],['Domestic route disruption',.79,.90,9,5],['Demand surge +30%',.74,.85,13,8],['Dual-source qualification delay',.70,.83,18,11],['Critical spare outage',.66,.81,22,13],['Multi-event stress',.57,.74,28,19],['Routine variability',.88,.93,6,4]],
        columns=['scenario','baseline_capacity_retention','semiconflow_capacity_retention','baseline_shortage_days','semiconflow_shortage_days'])
    return tech,df,cap,val

tech,crit,cap,val=build_data()

st.markdown('''<div class="hero"><span class="badge">NESFIC 2026 · Stream 2 · Track A</span><span class="badge">Working prototype</span><span class="badge">OR + Decision Science</span><h1>SemiconFlow-NE</h1><p>Technology-gated semiconductor supply-chain resilience, critical-material planning and localization decision support for Assam's emerging semiconductor ecosystem.</p></div>''',unsafe_allow_html=True)
st.info('This public prototype uses synthetic, industry-inspired data only. It contains no Tata Electronics, Government, supplier or other confidential operational data. All numerical performance evidence is synthetic demonstration evidence.')

tabs=st.tabs(['Executive','Dependency Map','Critical Inputs','Scenario Lab','Localization','Buffer Optimizer','Validation','Data & Governance','Demo Guide'])

with tabs[0]:
    st.subheader('The decision problem')
    st.markdown('A semiconductor assembly/test ecosystem can have equipment and nominal production capacity available but still lose **executable capacity** when a technology-critical, qualified input is unavailable. SemiconFlow-NE links materials, qualification, suppliers, inventory and logistics to actual production capability.')
    c1,c2,c3,c4=st.columns(4)
    c1.metric('Technology families',len(tech)); c2.metric('Critical input categories',len(crit)); c3.metric('High-risk inputs',int((crit.risk_band=='HIGH').sum())); c4.metric('Strategic localization candidates',int((crit.localization_score>=72).sum()))
    chart=cap.copy(); chart['Nominal']=100; chart['Executable']=100*chart.executable_capacity_index
    fig=px.bar(chart,x='technology',y=['Nominal','Executable'],barmode='group',labels={'value':'Capacity index (%)','variable':'Measure'}); fig.update_layout(height=390,legend_orientation='h'); st.plotly_chart(fig,use_container_width=True)
    st.markdown('#### Closed-loop architecture')
    st.markdown('**Materials + suppliers + qualification + inventory + logistics → technology dependency graph → executable-capacity engine → disruption scenarios → buffer/sourcing/localization optimization → explainable recommendation → human decision**')

with tabs[1]:
    st.subheader('Technology dependency map')
    tname=st.selectbox('Technology family',tech.technology.tolist()); tid=tech.loc[tech.technology==tname,'tech_id'].iloc[0]; d=crit[crit.tech_id==tid].sort_values(['criticality','risk_score'],ascending=False)
    c1,c2,c3=st.columns(3); c1.metric('Mapped dependencies',len(d)); c2.metric('High-risk gates',int((d.risk_band=='HIGH').sum())); c3.metric('Current binding input',cap.loc[cap.tech_id==tid,'binding_input'].iloc[0])
    st.dataframe(d[['material','function','criticality','days_cover','supplier','region','lead_time_days','risk_score','risk_band']],use_container_width=True,hide_index=True,height=410)
    labels=[tname]+d.material.tolist()+d.supplier.tolist(); idx={v:i for i,v in enumerate(labels)}; source=[]; target=[]; value=[]
    for _,r in d.iterrows(): source += [idx[tname],idx[r.material]]; target += [idx[r.material],idx[r.supplier]]; value += [max(.2,float(r.criticality)),max(.2,float(r.criticality))]
    fig=go.Figure(go.Sankey(node=dict(label=labels,pad=12,thickness=13),link=dict(source=source,target=target,value=value))); fig.update_layout(height=530,title='Illustrative technology → critical input → primary supplier map'); st.plotly_chart(fig,use_container_width=True)

with tabs[2]:
    st.subheader('Critical-material control tower')
    rb=st.multiselect('Risk band',['HIGH','MEDIUM','LOW'],default=['HIGH','MEDIUM']); q=crit[crit.risk_band.isin(rb)].sort_values(['risk_score','criticality'],ascending=False)
    c1,c2,c3,c4=st.columns(4); c1.metric('Inputs shown',len(q)); c2.metric('Median days of cover',f'{q.days_cover.median():.1f}'); c3.metric('External-source inputs',int((q.source_type=='External').sum())); c4.metric('Buffer gaps',int((q.buffer_gap_qty>0).sum()))
    st.dataframe(q[['risk_score','risk_band','material','tech_id','function','days_cover','lead_time_days','supplier','region','qualification_status','import_dependency','recommended_buffer_qty','buffer_gap_qty']],use_container_width=True,hide_index=True,height=480)
    fig=px.scatter(q,x='days_cover',y='risk_score',size=np.maximum(q.annual_spend_proxy_inr/1e6,1),hover_name='material',hover_data=['supplier','region','lead_time_days','import_dependency'],labels={'days_cover':'Days of cover','risk_score':'Composite risk score'}); fig.update_layout(height=420); st.plotly_chart(fig,use_container_width=True)

with tabs[3]:
    st.subheader('Disruption scenario lab')
    st.markdown('Change one disruption and immediately see the effect on material availability and technology-gated executable capacity.')
    scenario=st.radio('Scenario',['Supplier outage','Lead-time shock','Demand surge','Qualify alternate/local source'],horizontal=True)
    selected=st.selectbox('Critical input',crit.sort_values('risk_score',ascending=False).material.tolist()); r=crit[crit.material==selected].iloc[0]; tid=r.tech_id; tname=tech.loc[tech.tech_id==tid,'technology'].iloc[0]; base=float(cap.loc[cap.tech_id==tid,'executable_capacity_index'].iloc[0])
    a,b,c=st.columns(3); outage=a.slider('Disruption duration (days)',0,45,14,1); ltm=b.slider('Lead-time multiplier',1.0,2.5,1.4,.1); shock=c.slider('Demand shock',0,60,20,5)
    cover=float(r.days_cover); lead=float(r.lead_time_days)
    if scenario=='Supplier outage': cover=max(0,cover-outage); action='Activate a qualified alternate source; protect critical inventory; consider an expedited route.'
    elif scenario=='Lead-time shock': lead*=ltm; action='Increase temporary buffer; diversify route/source; review alternate-source qualification.'
    elif scenario=='Demand surge': cover=cover/(1+shock/100); action='Reallocate scarce material by technology priority and raise risk-adjusted replenishment.'
    else: cover+=min(12,.55*lead); lead=max(5,lead*.72); action='Complete qualification and shift a controlled allocation to the alternate/local source.'
    availability=float(np.clip((cover+.20*float(r.strategic_buffer_days))/(.9*lead+6),.05,1)); raw=float(np.clip(.52+.48*availability,.10,1))
    scen=float(np.clip(min(base,.68*base+.32*raw),.1,1)) if scenario!='Qualify alternate/local source' else float(np.clip(max(base,.72*base+.28*raw),0,1))
    c1,c2,c3,c4=st.columns(4); c1.metric('Affected technology',tname); c2.metric('Base executable capacity',f'{100*base:.1f}%'); c3.metric('Scenario executable capacity',f'{100*scen:.1f}%',delta=f'{100*(scen-base):+.1f} pp'); c4.metric('Capacity exposed',f'{100*max(0,base-scen):.1f} pp')
    st.markdown(f"<div class='callout'><b>Decision recommendation:</b> {action}<br><span class='smallnote'>Input: {selected} · Primary source: {r.supplier} ({r.region}) · Base cover: {r.days_cover:.1f} days</span></div>",unsafe_allow_html=True)
    st.warning('Scenario outputs are synthetic decision-support demonstrations. They are not estimates of any named company’s actual capacity or supply position.')

with tabs[4]:
    st.subheader('Assam / Northeast localization opportunity engine')
    st.markdown('This module ranks **illustrative input categories** for deeper local or domestic ecosystem development using technology criticality, external dependence, supplier concentration, lead time, spend proxy and localization feasibility.')
    n=st.slider('Show top opportunities',5,25,12); L=crit.sort_values('localization_score',ascending=False).head(n).copy(); L['priority']=np.where(L.localization_score>=72,'STRATEGIC',np.where(L.localization_score>=55,'PRIORITY','WATCH'))
    st.dataframe(L[['localization_score','priority','material','tech_id','criticality','import_dependency','supplier_concentration','lead_time_days','local_feasibility','risk_score']],use_container_width=True,hide_index=True)
    fig=px.bar(L.sort_values('localization_score'),x='localization_score',y='material',orientation='h',labels={'localization_score':'Localization opportunity score','material':''}); fig.update_layout(height=max(390,28*len(L))); st.plotly_chart(fig,use_container_width=True)
    st.caption('A high score is a screening signal, not an investment recommendation. Real localization decisions require technical qualification, quality, economics, environmental compliance, scale and supplier-development assessment.')

with tabs[5]:
    st.subheader('Risk-adjusted strategic buffer optimizer')
    selected=st.selectbox('Input category',crit.sort_values('risk_score',ascending=False).material.tolist(),key='buffer'); r=crit[crit.material==selected].iloc[0]
    x1,x2,x3=st.columns(3); service=x1.slider('Target service probability',.90,.995,float(r.target_service),.005); ltm=x2.slider('Lead-time scenario',.8,2.0,1.0,.1,key='blt'); emphasis=x3.slider('Resilience emphasis',.5,1.8,1.0,.1)
    # normal-quantile approximation adequate for demo slider
    z=float(np.interp(service,[.90,.95,.97,.98,.99,.995],[1.282,1.645,1.881,2.054,2.326,2.576])); daily=float(r.daily_requirement); cv=float(r.demand_cv); lead=float(r.lead_time_days)*ltm
    cycle=z*daily*cv*math.sqrt(max(1,lead)); rec=int(round(daily*emphasis*float(r.strategic_buffer_days)+cycle)); gap=max(0,rec-int(r.on_hand_qty)); value=gap*float(r.unit_cost_inr)
    c1,c2,c3,c4=st.columns(4); c1.metric('Current stock',f'{int(r.on_hand_qty):,}'); c2.metric('Recommended buffer',f'{rec:,}'); c3.metric('Incremental quantity',f'{gap:,}'); c4.metric('Incremental value proxy',f'₹{value:,.0f}')
    st.markdown('The buffer is **risk differentiated**: technology criticality, disruption exposure and lead-time uncertainty matter alongside statistical demand variability. It is not a blanket days-of-stock policy.')

with tabs[6]:
    st.subheader('Synthetic stress-test evidence')
    st.markdown('These results demonstrate computational behavior only; they are **not claims of achieved industry performance**.')
    m1=val.baseline_capacity_retention.mean(); m2=val.semiconflow_capacity_retention.mean(); s1=val.baseline_shortage_days.mean(); s2=val.semiconflow_shortage_days.mean()
    c1,c2,c3,c4=st.columns(4); c1.metric('Baseline capacity retention',f'{100*m1:.1f}%'); c2.metric('SemiconFlow retention',f'{100*m2:.1f}%',delta=f'{100*(m2-m1):+.1f} pp'); c3.metric('Baseline shortage duration',f'{s1:.1f} d'); c4.metric('SemiconFlow shortage duration',f'{s2:.1f} d',delta=f'{s2-s1:+.1f} d')
    vv=val.melt(id_vars=['scenario'],value_vars=['baseline_capacity_retention','semiconflow_capacity_retention'],var_name='policy',value_name='retention'); vv.retention*=100
    fig=px.bar(vv,x='scenario',y='retention',color='policy',barmode='group',labels={'retention':'Executable capacity retained (%)','scenario':'','policy':'Policy'}); fig.update_layout(height=430,xaxis_tickangle=-25); st.plotly_chart(fig,use_container_width=True); st.dataframe(val,use_container_width=True,hide_index=True)

with tabs[7]:
    st.subheader('Data requirements, controls and public context')
    st.markdown('#### Production data requested only after authorization')
    st.markdown('- Material/component/consumable master and technology compatibility\n- Supplier master, approved-source status and qualification state\n- Purchase orders, receipts, supplier lead times and disruptions\n- Inventory snapshots and buffer policies\n- Production plan or technology-level material requirements\n- Logistics route and transit-time history\n- Critical spare/test-interface availability where relevant\n- Cost and service parameters required for optimization')
    a,b,c=st.columns(3)
    with a: st.markdown('**No confidential data in public demo**\n\nSynthetic data only; no named-company BOM, supplier allocation, production schedule or internal inventory.')
    with b: st.markdown('**Human decision control**\n\nRecommendations are advisory. Qualification, sourcing, buffer and localization decisions require authorised technical/commercial approval.')
    with c: st.markdown('**Auditability**\n\nProduction deployment would version data, models, scenarios, recommendations, overrides and approvals.')
    st.markdown('#### Public context used to frame the problem')
    st.markdown('- [Advantage Assam — Electronics and Semiconductors](https://www.advantageassam.assam.gov.in/sectors/electronics-and-semiconductors)\n- [Tata Group — semiconductor assembly and test facility in Assam](https://www.tata.com/newsroom/business/first-indian-semiconductor-assembly-test-facility)\n- [PIB — India Building Semiconductor Future / Semicon 2.0](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2311220&lang=1&reg=48)')
    st.caption('These links establish public ecosystem context only; they do not imply access to or endorsement by the organisations.')

with tabs[8]:
    st.subheader('90-second evaluator demo')
    st.markdown('**1. Executive (15 s):** show nominal versus executable capacity.\n\n**2. Dependency Map (15 s):** choose Flip Chip or Wire Bond and show material/supplier gates.\n\n**3. Critical Inputs (10 s):** show which inputs are high risk and why.\n\n**4. Scenario Lab (25 s):** simulate a supplier outage or lead-time shock and show capacity impact plus recommended action.\n\n**5. Localization (15 s):** show ranked Assam/Northeast localization opportunities and explain that it is a screening tool.\n\n**6. Validation (10 s):** show synthetic stress-test evidence and state that real impact would be validated only on authorised data.')
    st.success('SemiconFlow-NE tells planners which qualified material, supplier or logistics dependency can constrain executable semiconductor production, what the likely impact is, and which sourcing, buffer or localization action best improves resilience.')
    st.error('Do not claim access to Tata Electronics data, knowledge of its internal suppliers/BOM, endorsement by Government or industry, or that synthetic results are real operational outcomes.')
