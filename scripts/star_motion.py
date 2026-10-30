"""Fit a five-point star to the fixed-length orthogonal-slider workspace.

A=(L*cos(theta),0), B=(0,-L*sin(theta)), P=(1-u)*A+u*B.
The trace stays ON the connector, and |A-B| is always L.
"""
import math

def star_vertices():
    return [(math.sin(i*math.pi/5)*(1 if i%2==0 else .44),
             -math.cos(i*math.pi/5)*(1 if i%2==0 else .44)) for i in range(10)]

def candidates(offset):
    verts=[(x,y+offset) for x,y in star_vertices()]
    items=[]
    for i,a in enumerate(verts):
        b=verts[(i+1)%10];dx,dy=b[0]-a[0],b[1]-a[1]
        cuts={0.,1.}
        if dx and 0 < -a[0]/dx < 1:cuts.add(-a[0]/dx)
        if dy and 0 < -a[1]/dy < 1:cuts.add(-a[1]/dy)
        cuts=sorted(cuts)
        tests=set(cuts)
        for lo,hi in zip(cuts,cuts[1:]):
            mid=(lo+hi)/2;sx=1 if a[0]+dx*mid>=0 else -1;sy=1 if a[1]+dy*mid>=0 else -1
            ax,ay=sx*a[0],sy*a[1];vx,vy=sx*dx,sy*dy
            if vx*vy<0:
                ratio=(-vy/vx)**3
                t=(ratio*ax-ay)/(vy-ratio*vx)
                if lo<t<hi:tests.add(t)
        for t in tests:
            x,y=a[0]+dx*t,a[1]+dy*t;q=abs(x)**(2/3)+abs(y)**(2/3)
            items.append((q,i+t,x,y))
    return verts,items

def solve_star(samples_per_edge=240):
    lo,hi=-.6,.6
    for _ in range(85):
        off=(lo+hi)/2;_,items=candidates(off)
        top=max(q for q,_,_,y in items if y<=0);bottom=max(q for q,_,_,y in items if y>=0)
        if top>bottom:lo=off
        else:hi=off
    offset=(lo+hi)/2;verts,items=candidates(offset);peak=max(x[0] for x in items);scale=peak**(-1.5)
    touches=sorted(set(round(pos,10) for q,pos,x,y in items if abs(q-peak)<1e-9 and abs(x)>1e-8))
    assert len(touches)==4,(offset,touches)
    # The two inverse branches join exactly at these four workspace tangencies.
    def pose(x,y,upper):
        if abs(x)<1e-12:
            return (math.pi/2 if y<0 else -math.pi/2),abs(y)
        if abs(y)<1e-12:
            return (0 if x>0 else math.pi),1-abs(x)
        k=abs(y)**(2/3)/(abs(x)**(2/3)+abs(y)**(2/3))
        def f(u):return x*x/(1-u)**2+y*y/u**2-1
        if abs(f(k))<1e-12:u=k
        else:
            assert f(k)<1e-9,f(k)
            a,b=(k,1-1e-14) if upper else (1e-14,k)
            for _ in range(70):
                m=(a+b)/2
                if (f(m)>0)==upper:b=m
                else:a=m
            u=(a+b)/2
        return math.atan2(-y/u,x/(1-u)),u
    rows=[];targets=[];previous=None
    for j in range(samples_per_edge*10+1):
        s=j/samples_per_edge;i=min(9,int(s));v=s-i
        # Ease at sharp vertices, so both sliders turn continuously at tips.
        v=(1-math.cos(v*math.pi))/2
        a,b=verts[i],verts[(i+1)%10];x=scale*(a[0]+(b[0]-a[0])*v);y=scale*(a[1]+(b[1]-a[1])*v)
        count=sum(t<s-1e-9 for t in touches)
        theta,u=pose(x,y,bool(count%2))
        if previous is not None:theta+=round((previous-theta)/math.tau)*math.tau
        previous=theta;rows.append([j/(samples_per_edge*10)*math.tau,theta,u]);targets.append([x,y])
    max_error=max(math.hypot((1-u)*math.cos(t)-x,-u*math.sin(t)-y) for (_,t,u),(x,y) in zip(rows,targets))
    assert max_error<1e-7,max_error
    assert all(0<=u<=1 for _,_,u in rows)
    return {'rows':rows,'targets':targets,'offset':offset,'scale':scale,'touches':touches,'max_error':max_error}

if __name__=='__main__':
    import json
    s=solve_star();print(json.dumps({k:v for k,v in s.items() if k not in ('rows','targets')},indent=2))
