"""Recompute heart slider poses from an analytic curve; no imported motion table."""
import math

def curve(t):
    return math.sin(t)**3, -(13*math.cos(t)-5*math.cos(2*t)-2*math.cos(3*t)-math.cos(4*t))/16

def extrema(offset):
    def score(t):
        x,y=curve(t)
        return abs(x)**(2/3)+abs(y+offset)**(2/3)
    size=240;step=math.pi/size
    values=[score(i*step) for i in range(size+1)]
    candidates=[(values[0],0.),(values[-1],math.pi)]
    for i in range(1,size):
        if values[i]>=values[i-1] and values[i]>=values[i+1]:
            a,b=(i-1)*step,(i+1)*step
            for _ in range(65):
                l=a+(b-a)*.3819660112501051;r=a+(b-a)*.6180339887498949
                if score(l)>score(r):b=r
                else:a=l
            t=(a+b)/2;candidates.append((score(t),t))
    above=max((q,t) for q,t in candidates if curve(t)[1]+offset<=0)
    below=max((q,t) for q,t in candidates if curve(t)[1]+offset>=0)
    return above,below

def solve_heart():
    a,b=-.2,.3
    for _ in range(65):
        offset=(a+b)/2;top,bottom=extrema(offset)
        if top[0]>bottom[0]:a=offset
        else:b=offset
    offset=(a+b)/2;top,bottom=extrema(offset);scale=max(top[0],bottom[0])**(-1.5)
    touches=sorted([top[1],bottom[1],math.tau-bottom[1],math.tau-top[1]])
    rows=[];previous=None;max_error=0
    for i in range(3601):
        phase=i/3600*math.tau;x,y=curve(phase);x*=scale;y=(y+offset)*scale
        upper=sum(t<phase for t in touches)%2==1
        if abs(x)<1e-13:
            ratio=abs(y);angle=math.copysign(math.pi/2,-y)
        elif abs(y)<1e-13:
            ratio=1-abs(x);angle=0 if x>0 else math.pi
        else:
            minimum=abs(y)**(2/3)/(abs(x)**(2/3)+abs(y)**(2/3))
            def residual(r):return x*x/(1-r)**2+y*y/r**2-1
            assert residual(minimum)<1e-9
            if abs(residual(minimum))<1e-13:ratio=minimum
            else:
                low,high=(minimum,1-1e-14) if upper else (1e-14,minimum)
                for _ in range(65):
                    middle=(low+high)/2
                    if (residual(middle)>0)==upper:high=middle
                    else:low=middle
                ratio=(low+high)/2
            angle=math.atan2(-y/ratio,x/(1-ratio))
        if previous is not None:angle+=round((previous-angle)/math.tau)*math.tau
        previous=angle
        max_error=max(max_error,math.hypot((1-ratio)*math.cos(angle)-x,-ratio*math.sin(angle)-y))
        rows.append([phase,angle,ratio])
    assert max_error<1e-7
    return {'rows':rows,'offset':offset,'scale':scale,'max_error':max_error,'touches':touches}

if __name__=='__main__':
    s=solve_heart();print({k:v for k,v in s.items() if k!='rows'})
