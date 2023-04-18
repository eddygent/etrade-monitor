from datetime import datetime

st = "BAC Apr 21 '23 $30 Call"

sym,m,d,y,p,t = st.split(" ")
combined = "-".join([m,d,y.strip("'")])
dto = datetime.strptime(combined, "%b-%d-%y")
price = p.strip("$")
_type = t

print(dto, _type)
