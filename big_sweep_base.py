import numpy as np
import pandas as pd
from collections import defaultdict
from pulp import (LpVariable, LpProblem, LpMinimize, lpSum, LpStatus, value,
                  CPLEX_CMD, PULP_CBC_CMD, PulpSolverError)

# ---------------- data load / clean / region (identical to the base model) ----------------
xl = pd.ExcelFile('Backend//Data_11.xlsx')
PC   = pd.read_excel(xl, 'A.1 Warehouse'); Mill = pd.read_excel(xl, 'A.2 FPS')
WH   = pd.read_excel(xl, 'A.2 Warehouse'); SP   = pd.read_excel(xl, 'A.3 Storage')
RH   = pd.read_excel(xl, 'A.3 RH');        RHMap= pd.read_excel(xl, 'RHMap')

def clean(s): return s.astype(str).str.lower().str.replace(r'\s+', '', regex=True)
PC['District']=clean(PC['WH_District']);   Mill['District']=clean(Mill['FPS_District'])
WH['District']=clean(WH['SW_District']);    SP['District']=clean(SP['WH_District']);   RH['District']=clean(RH['WH_District'])
for df in (PC,Mill,WH,SP,RH):
    df['District']=df['District'].replace({'thiruvallur':'thiruvalluvar','thiruvallore':'thiruvalluvar'})
PC['Region']=PC['Unnamed: 8']; Mill['Region']=Mill['Unnamed: 11']; WH['Region']=WH['Unnamed: 8']
SP['Region']=SP['Unnamed: 8']; RH['Region']=RH['quantity of Wheat stored (Quintals)']
_all=pd.concat([d[['District','Region']] for d in (PC,Mill,WH,SP,RH)])
district_region=_all.dropna().drop_duplicates().set_index('District')['Region'].to_dict()
for df in (PC,Mill,WH,SP,RH): df['Region']=df['District'].map(district_region)
def idx(df,r): return list(df.index[df['Region']==r])
PC_S,PC_D=idx(PC,'Surplus'),idx(PC,'Deficit');     Mill_S,Mill_D=idx(Mill,'Surplus'),idx(Mill,'Deficit')
SP_S,SP_D=idx(SP,'Surplus'),idx(SP,'Deficit');     WH_S,WH_D=idx(WH,'Surplus'),idx(WH,'Deficit')
RH_S,RH_D=idx(RH,'Surplus'),idx(RH,'Deficit')
print('nodes  PC',len(PC),'Mill',len(Mill),'SP',len(SP),'RH',len(RH),'WH',len(WH))

# ---------------- geometry + arc builder (district rule + E2 accessibility hook) ----------------
def haversine_km(lat1,lon1,lat2,lon2):
    R=6371.0; p1,p2=np.radians(lat1),np.radians(lat2)
    dp,dl=p2-p1,np.radians(lon2-lon1)
    a=np.sin(dp/2)**2+np.cos(p1)*np.cos(p2)*np.sin(dl/2)**2
    return R*2*np.arctan2(np.sqrt(a),np.sqrt(1-a))

def build_arc(src_df,slat,slon,src_idx,dst_df,dlat,dlon,dst_idx,
              max_km=None, src_dcol=None, dst_dcol=None):
    src_idx,dst_idx=list(src_idx),list(dst_idx)
    sl,so=src_df.loc[src_idx,slat].to_numpy(),src_df.loc[src_idx,slon].to_numpy()
    dl,do=dst_df.loc[dst_idx,dlat].to_numpy(),dst_df.loc[dst_idx,dlon].to_numpy()
    D=haversine_km(sl[:,None],so[:,None],dl[None,:],do[None,:])
    keep=np.ones(D.shape,dtype=bool)
    if max_km is not None: keep&=(D<max_km)
    if src_dcol is not None and dst_dcol is not None:                      # same-district rule
        sd=src_df.loc[src_idx,src_dcol].to_numpy().astype(str); dd=dst_df.loc[dst_idx,dst_dcol].to_numpy().astype(str)
        keep_d=keep&(sd[:,None]==dd[None,:]); no=~keep_d.any(axis=1)
        for r in np.nonzero(no)[0]:
            al=np.nonzero(keep[r])[0]
            if al.size: keep_d[r,al[np.argmin(D[r,al])]]=True
        keep=keep_d
    a_,b_=np.nonzero(keep)
    return {(src_idx[x],dst_idx[y]):float(D[x,y]) for x,y in zip(a_,b_)}

def add_supply_fallback(tagd,src_df,slat,slon,src_idx,dst_df,dlat,dlon,dst_idx,supply_col,cap_col,a,margin=1.3):
    src_idx,dst_idx=list(src_idx),list(dst_idx)
    src_by=defaultdict(list)
    for i in src_idx: src_by[src_df.at[i,'District']].append(i)
    dst_by=defaultdict(list)
    for j in dst_idx: dst_by[dst_df.at[j,'District']].append(j)
    free={}
    for d,pcs in src_by.items():
        free[d]=max(0.0,sum(src_df.at[i,supply_col] for i in pcs)-a*sum(dst_df.at[j,cap_col] for j in dst_by.get(d,[])))
    shorts=[]
    for dist,mills in dst_by.items():
        short=a*sum(dst_df.at[j,cap_col] for j in mills)-sum(src_df.at[i,supply_col] for i in src_by.get(dist,[]))
        if short>1: shorts.append((short,dist,mills))
    shorts.sort(reverse=True); added=0
    for short,dist,mills in shorts:
        mlat=dst_df.loc[mills,dlat].to_numpy(); mlon=dst_df.loc[mills,dlon].to_numpy()
        cand=[]
        for i in src_idx:
            d=src_df.at[i,'District']
            if d==dist or free.get(d,0)<=0: continue
            cand.append((float(haversine_km(src_df.at[i,slat],src_df.at[i,slon],mlat,mlon).min()),i))
        cand.sort(); acc=0.0
        for _,i in cand:
            d=src_df.at[i,'District']
            if free.get(d,0)<=0: continue
            for j in mills:
                if (i,j) not in tagd:
                    tagd[(i,j)]=float(haversine_km(src_df.at[i,slat],src_df.at[i,slon],dst_df.at[j,dlat],dst_df.at[j,dlon])); added+=1
            take=min(src_df.at[i,supply_col],free[d]); free[d]-=take; acc+=take
            if acc>=short*margin: break
    return added

def connect_knn(tagd,src_df,slat,slon,src_idx,dst_df,dlat,dlon,dst_idx,k=6):
    dla=dst_df.loc[dst_idx,dlat].to_numpy(); dlo=dst_df.loc[dst_idx,dlon].to_numpy(); da=list(dst_idx); added=0
    for i in src_idx:
        Di=haversine_km(src_df.at[i,slat],src_df.at[i,slon],dla,dlo)
        for pos in np.argsort(Di)[:k]:
            j=da[pos]
            if (i,j) not in tagd: tagd[(i,j)]=float(Di[pos]); added+=1
    return added

# ===================== ENHANCEMENT SWITCHES & PARAMETERS =====================
CONV = 0.67          # paddy -> rice outturn
A_RULE = 0.225       # direct-from-PC fraction of mill capacity (surplus ==, deficit <=)
BIG = 10000          # unmet-demand penalty

# E1 - minimum mill utilisation (0.0 = off).  mill paddy-in >= U_MIN * capacity
U_MIN = 0.0

# E2 - road accessibility.  Plug real data here; defaults => every pair accessible, haversine distance.
def accessible_fn(tag, i, j):      # return False to forbid the road arc (i->j) of this tag
    return True
def road_dist_fn(tag, i, j, hav):  # return the road-network distance; default = straight-line
    return hav
USE_E2 = False       # True -> apply accessible_fn / road_dist_fn

# E3 - railhead capacity.  ENFORCE_RH_CAP already matches the base model; RH_CAP_SCALE tightens/loosens it.
ENFORCE_RH_CAP = True
RH_CAP_SCALE = 1.0

# E4 - threshold / mode choice
D_KM = 150           # the road/rail threshold (E4a sweeps this)
COST_BASED = False   # E4b: True => no distance cap on PC_S->SP_D road; choose road vs rail by cost
C_ROAD = 1.0         # per quintal-km road cost  (E4b)
C_RAIL = 0.3         # per quintal-km rail cost   (E4b)

CPLEX_PATH = r"C:\Program Files\IBM\ILOG\CPLEX_Studio222\cplex\bin\x64_win64\cplex.exe"
print('config loaded')

# ---------------- build all road/rail arcs for a given threshold & mode (E4a/E4b aware) ----------------
def build_arcs(d_km=150, cost_based=False, c_road=1.0, c_rail=0.3, use_e2=False):
    DD=dict(src_dcol='District',dst_dcol='District')
    # surplus->deficit road cap: removed when cost_based (E4b)
    spd_max = None if cost_based else d_km+1e-6
    Distance={
     'PCS_MILLS': build_arc(PC,'WH_Lat','WH_Long',PC_S,Mill,'FPS_Lat','FPS_Long',Mill_S,**DD),
     'PCS_SPS':   build_arc(PC,'WH_Lat','WH_Long',PC_S,SP,'WH_Lat','WH_Long',SP_S,**DD),
     'SPS_MILLS': build_arc(SP,'WH_Lat','WH_Long',SP_S,Mill,'FPS_Lat','FPS_Long',Mill_S,**DD),
     'MILLS_SWS': build_arc(Mill,'FPS_Lat','FPS_Long',Mill_S,WH,'SW_Lat','SW_Long',WH_S,**DD),
     'PCS_RHS':   build_arc(PC,'WH_Lat','WH_Long',PC_S,RH,'WH_Lat','WH_Long',RH_S,**DD),
     'PCS_SPD':   build_arc(PC,'WH_Lat','WH_Long',PC_S,SP,'WH_Lat','WH_Long',SP_D,max_km=spd_max),
     'PCD_SPD':   build_arc(PC,'WH_Lat','WH_Long',PC_D,SP,'WH_Lat','WH_Long',SP_D,**DD),
     'PCD_MILLD': build_arc(PC,'WH_Lat','WH_Long',PC_D,Mill,'FPS_Lat','FPS_Long',Mill_D,**DD),
     'SPD_MILLD': build_arc(SP,'WH_Lat','WH_Long',SP_D,Mill,'FPS_Lat','FPS_Long',Mill_D,**DD),
     'RHD_MILLD': build_arc(RH,'WH_Lat','WH_Long',RH_D,Mill,'FPS_Lat','FPS_Long',Mill_D,**DD),
     'MILLD_SWD': build_arc(Mill,'FPS_Lat','FPS_Long',Mill_D,WH,'SW_Lat','SW_Long',WH_D,**DD),
    }
    add_supply_fallback(Distance['PCS_MILLS'],PC,'WH_Lat','WH_Long',PC_S,Mill,'FPS_Lat','FPS_Long',Mill_S,'Paddy_Procurement','Mill_Capacity',A_RULE)
    connect_knn(Distance['PCD_MILLD'],PC,'WH_Lat','WH_Long',PC_D,Mill,'FPS_Lat','FPS_Long',Mill_D,k=6)
    connect_knn(Distance['SPD_MILLD'],SP,'WH_Lat','WH_Long',SP_D,Mill,'FPS_Lat','FPS_Long',Mill_D,k=6)

    # ---- rail split from RHMap ----
    RM=RHMap.rename(columns={RHMap.columns[2]:'From_RH',RHMap.columns[5]:'To_RH',RHMap.columns[8]:'Qty'})
    RM['From_RH']=RM['From_RH'].astype(str); RM['To_RH']=RM['To_RH'].astype(str); RH['WH_ID']=RH['WH_ID'].astype(str)
    pos={rid:i for i,rid in RH['WH_ID'].items()}; RM['i']=RM['From_RH'].map(pos); RM['j']=RM['To_RH'].map(pos)
    us=RM.dropna(subset=['i','j','Qty']).copy(); us['i']=us['i'].astype(int); us['j']=us['j'].astype(int)
    us=us[us['i'].isin(RH_S)&us['j'].isin(RH_D)]; us['share']=us['Qty']/us.groupby('i')['Qty'].transform('sum')
    dest_of=defaultdict(list); src_of=defaultdict(list)
    for r_ in us.itertuples(): dest_of[r_.i].append((r_.j,r_.share)); src_of[r_.j].append((r_.i,r_.share))

    # ---- far PC_S->SP_D rail routing (pairs beyond d_km) ----
    pcl,pco=PC.loc[PC_S,'WH_Lat'].to_numpy(),PC.loc[PC_S,'WH_Long'].to_numpy()
    spl,spo=SP.loc[SP_D,'WH_Lat'].to_numpy(),SP.loc[SP_D,'WH_Long'].to_numpy()
    rhl,rho=RH['WH_Lat'].to_numpy(),RH['WH_Long'].to_numpy()
    Droad=haversine_km(pcl[:,None],pco[:,None],spl[None,:],spo[None,:]); near=Droad<d_km+1e-6
    rr=sorted(dest_of); costs=[]; railkm=[]
    for r in rr:
        leg1=haversine_km(pcl,pco,rhl[r],rho[r])
        leg2=sum(sh*haversine_km(rhl[s],rho[s],spl,spo) for s,sh in dest_of[r])
        railleg=sum(sh*haversine_km(rhl[r],rho[r],rhl[s],rho[s]) for s,sh in dest_of[r])  # RH_S->RH_D rail km
        costs.append(leg1[:,None]+leg2[None,:]); railkm.append(np.full_like(leg2,railleg)[None,:]+0*leg1[:,None])
    costs=np.stack(costs); railkm=np.stack(railkm); br,bc=costs.argmin(axis=0),costs.min(axis=0)
    Distance['PCS_SPD_RAIL']={}; RailVia={}
    for a_,b_ in zip(*np.nonzero(~near)):
        i,j=PC_S[a_],SP_D[b_]; r=rr[br[a_,b_]]
        road_legs=float(bc[a_,b_]); rail_leg=float(railkm[br[a_,b_],a_,b_])
        # base: coefficient = road legs (rail free). E4b: c_road*road_legs + c_rail*rail_leg
        Distance['PCS_SPD_RAIL'][(i,j)]= (c_road*road_legs + c_rail*rail_leg) if cost_based else road_legs
        RailVia[(i,j)]=r

    # ---- E4b: scale every ROAD-arc coefficient by c_road so road competes with rail by cost ----
    if cost_based:
        for t in Distance:
            if t=='PCS_SPD_RAIL': continue
            Distance[t]={k:c_road*v for k,v in Distance[t].items()}

    # ---- E2: accessibility pruning + road-network distance ----
    if use_e2:
        for t in Distance:
            if t=='PCS_SPD_RAIL': continue
            Distance[t]={k:road_dist_fn(t,k[0],k[1],v) for k,v in Distance[t].items() if accessible_fn(t,k[0],k[1])}
    return Distance, RailVia, dest_of, src_of

print('build_arcs ready')

# ---------------- build & solve the model (base + E1 + E3) ----------------
def solve_model(d_km=150, u_min=0.0, enforce_rh_cap=True, rh_cap_scale=1.0,
                cost_based=False, c_road=1.0, c_rail=0.3, use_e2=False,
                solver='cplex', msg=False, time_limit=1800):
    Distance, RailVia, dest_of, src_of = build_arcs(d_km, cost_based, c_road, c_rail, use_e2)
    Allocation={tag:{(i,j):LpVariable(f"X_{tag}_{i}_{j}",lowBound=0) for (i,j) in dd} for tag,dd in Distance.items()}
    m=LpProblem("Enhanced_Model",LpMinimize); Mill_S_set=set(Mill_S)
    def flows(spec):
        d=defaultdict(list)
        for tag,end in spec:
            for key,var in Allocation[tag].items(): d[key[end]].append(var)
        return d
    Unmet={j:LpVariable(f"Unmet_{j}",lowBound=0) for j in WH_S+WH_D}
    m += lpSum(Distance[t][k]*Allocation[t][k] for t in Allocation for k in Allocation[t]) + BIG*lpSum(Unmet.values())

    XR=Allocation['PCS_SPD_RAIL']; XR_i=defaultdict(list); XR_j=defaultdict(list); XR_r=defaultdict(list)
    for (i,j),v in XR.items(): XR_i[i].append(v); XR_j[j].append(v); XR_r[RailVia[(i,j)]].append(v)

    pc_out=flows([('PCS_MILLS',0),('PCS_SPS',0),('PCS_RHS',0),('PCS_SPD',0),('PCD_SPD',0),('PCD_MILLD',0)])
    for i in set(pc_out)|set(XR_i):
        m += lpSum(pc_out[i])+lpSum(XR_i[i])==PC.at[i,'Paddy_Procurement'], f"PC_supply_{i}"

    mill_pc=flows([('PCS_MILLS',1),('PCD_MILLD',1)])
    mill_in=flows([('PCS_MILLS',1),('SPS_MILLS',1),('PCD_MILLD',1),('SPD_MILLD',1),('RHD_MILLD',1)])
    mill_out=flows([('MILLS_SWS',0),('MILLD_SWD',0)])
    for mm in set(mill_in)|set(mill_out):
        cap=Mill.at[mm,'Mill_Capacity']
        if mill_pc[mm]:
            if mm in Mill_S_set: m += lpSum(mill_pc[mm])==A_RULE*cap, f"Mill_a_{mm}"
            else:                m += lpSum(mill_pc[mm])<=A_RULE*cap, f"Mill_a_{mm}"
        if mill_in[mm]:
            m += lpSum(mill_in[mm])<=cap, f"Mill_cap_{mm}"
            if u_min>0:                                        # ---- E1: minimum mill utilisation ----
                m += lpSum(mill_in[mm])>=u_min*cap, f"Mill_min_{mm}"
        if mill_in[mm] or mill_out[mm]:
            m += lpSum(mill_out[mm])==CONV*lpSum(mill_in[mm]), f"Mill_bal_{mm}"

    sp_in=flows([('PCS_SPS',1),('PCS_SPD',1),('PCD_SPD',1)]); sp_out=flows([('SPS_MILLS',0),('SPD_MILLD',0)])
    for s_ in set(sp_in)|set(sp_out)|set(XR_j):
        inflow=lpSum(sp_in[s_])+lpSum(XR_j[s_])
        if sp_out[s_] or len(inflow)>0: m += inflow==lpSum(sp_out[s_]), f"SP_bal_{s_}"
        if len(inflow)>0:               m += inflow<=SP.at[s_,'Capacity'], f"SP_cap_{s_}"

    pcrh=flows([('PCS_RHS',1)]); rhd_out=flows([('RHD_MILLD',0)]); in_r={}
    for r in RH_S:
        in_r[r]=lpSum(pcrh[r])+lpSum(XR_r[r])
        if len(in_r[r])==0: continue
        if r in dest_of:
            if enforce_rh_cap: m += in_r[r]<=rh_cap_scale*RH.at[r,'Capacity'], f"RH_cap_{r}"   # ---- E3 ----
        else: m += in_r[r]==0, f"RH_nomap_{r}"
    for s_ in RH_D:
        it=lpSum(sh*in_r[r] for r,sh in src_of[s_]); im=lpSum(sh*lpSum(pcrh[r]) for r,sh in src_of[s_])
        if len(im)>0 or rhd_out[s_]: m += im==lpSum(rhd_out[s_]), f"RH_bal_{s_}"
        if enforce_rh_cap and len(it)>0: m += it<=rh_cap_scale*RH.at[s_,'Capacity'], f"RH_capD_{s_}"  # ---- E3 ----

    wh_in=flows([('MILLS_SWS',1),('MILLD_SWD',1)])
    for j in WH_S+WH_D: m += lpSum(wh_in[j])+Unmet[j]>=WH.at[j,'Annual_Demand'], f"WH_{j}"

    # NOTE: PuLP's CPLEX_CMD raises PulpSolverError on an infeasible/unbounded result instead of
    # returning a status, so we catch it and report 'Infeasible' gracefully (important for the sweeps).
    try:
        if solver=='cplex': m.solve(CPLEX_CMD(path=CPLEX_PATH,msg=msg,timeLimit=time_limit))
        else:               m.solve(PULP_CBC_CMD(msg=msg,timeLimit=time_limit))
        status=LpStatus[m.status]
    except PulpSolverError:
        return {'status':'Infeasible','objective':None,'transport':0.0,'unmet':0.0,'rail_share':0.0,
                'pcs_spd_road':0.0,'pcs_spd_rail':0.0,'n_vars':len(m.variables()),
                'n_cons':len(m.constraints),'Allocation':Allocation,'Distance':Distance}

    transport=sum(Distance[t][k]*(v.varValue or 0) for t in Allocation for k,v in Allocation[t].items())
    unmet=sum(v.varValue or 0 for v in Unmet.values())
    spd =sum(v.varValue or 0 for v in Allocation['PCS_SPD'].values())
    sprl=sum(v.varValue or 0 for v in Allocation['PCS_SPD_RAIL'].values())
    rail_share = sprl/(spd+sprl) if (spd+sprl)>0 else 0.0
    return {'status':status,'objective':value(m.objective),'transport':transport,
            'unmet':unmet,'rail_share':rail_share,'pcs_spd_road':spd,'pcs_spd_rail':sprl,
            'n_vars':len(m.variables()),'n_cons':len(m.constraints),
            'Allocation':Allocation,'Distance':Distance,'Unmet':Unmet,
            'RailVia':RailVia,'dest_of':dest_of,'src_of':src_of,'u_min':u_min,'d_km':d_km,
            'cost_based':cost_based}

print('solve_model ready')

