"""Fit a finite planar contour into one continuous inverse-kinematics branch.

Coordinates supplied by the model use x-right, y-up. No eval, model service,
third-party package, or hardcoded catalogue of named silhouettes is required.
"""
import bisect
import math

COLORS = {'auto', 'ice', 'rose', 'gold', 'violet'}
KINDS = {'circle', 'heart', 'star', 'polygon', 'radial-star', 'path'}

def number(value, name, limit=1e6):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(name + '必须是数值')
    if not math.isfinite(value) or abs(value) > limit:
        raise ValueError(name + '必须是范围内的有限数值')
    return value

def validate(config):
    if not isinstance(config, dict):
        raise ValueError('配置必须是对象')
    kind = config.get('shape')
    if not isinstance(kind, str) or kind not in KINDS:
        raise ValueError('请用polygon生成正多边形，或用path提供自定义轮廓点')
    allowed = {'shape', 'color', 'label'}
    if kind == 'polygon': allowed |= {'sides', 'rotation'}
    if kind == 'radial-star': allowed |= {'tips', 'inner_ratio', 'rotation'}
    if kind == 'path': allowed |= {'points', 'closed'}
    if set(config) - allowed:
        raise ValueError('包含该形状不支持的字段：' + ','.join(sorted(set(config)-allowed)))
    color = config.get('color', 'auto')
    if not isinstance(color, str) or color not in COLORS:
        raise ValueError('颜色可选auto、ice、rose、gold、violet')
    if 'label' in config and (not isinstance(config['label'], str) or not 1 <= len(config['label']) <= 24):
        raise ValueError('label应为1至24字的形状名称')
    if kind in ('polygon', 'radial-star'):
        field = 'sides' if kind == 'polygon' else 'tips'
        count = config.get(field)
        if type(count) is not int or not 3 <= count <= 60:
            raise ValueError(field + '必须是3至60的整数')
        number(config.get('rotation', 90), 'rotation', 36000)
        if kind == 'radial-star' and not .05 <= number(config.get('inner_ratio', .45), 'inner_ratio') < 1:
            raise ValueError('内外半径比须在0.05至1之间（不含1）')
    if kind == 'path':
        if type(config.get('closed', True)) is not bool:
            raise ValueError('closed必须是true或false')
        points = config.get('points')
        if not isinstance(points, list) or not 2 <= len(points) <= 2048:
            raise ValueError('points需要2至2048个二维点；多个轮廓请分开制作')
        for point in points:
            if not isinstance(point, (list, tuple)) or len(point) != 2:
                raise ValueError('每个点应为[x,y]，不支持多轮廓嵌套')
            number(point[0], 'x'); number(point[1], 'y')

def vertices(config):
    kind = config['shape']
    if kind == 'path': return [tuple(point) for point in config['points']]
    count = config['sides'] if kind == 'polygon' else config['tips'] * 2
    angle = math.radians(config.get('rotation', 90))
    ratio = config.get('inner_ratio', .45)
    return [(math.cos(angle + math.tau*i/count)*(ratio if kind=='radial-star' and i%2 else 1),
             math.sin(angle + math.tau*i/count)*(ratio if kind=='radial-star' and i%2 else 1)) for i in range(count)]

def inverse(x, y):
    # x>0, y<0 and |x|^(2/3)+|y|^(2/3)<1: two roots exist.
    # Always choose the larger u root. This branch is continuous in our safe box.
    ax, ay = x**(2/3), (-y)**(2/3)
    low, high = ay/(ax+ay), 1-1e-14
    for _ in range(55):
        u = (low+high)/2
        if x*x/(1-u)**2 + y*y/u**2 > 1: high=u
        else: low=u
    u=(low+high)/2
    return math.atan2(-y/u,x/(1-u)),u

def solve_contour(config):
    validate(config)
    raw=vertices(config)
    clean=[]
    for point in raw:
        if not clean or point != clean[-1]: clean.append(point)
    closed=config.get('closed', True)
    if closed and len(clean)>1 and clean[0]==clean[-1]: clean.pop()
    if len(clean)<(3 if closed else 2):
        raise ValueError('轮廓去除相邻重复点后，闭合至少需要3点，开放至少2点')
    xs,ys=zip(*clean); width=max(xs)-min(xs);height=max(ys)-min(ys)
    span=max(width,height)
    if span<1e-10: raise ValueError('轮廓尺寸过小或所有点重合')
    cx=(max(xs)+min(xs))/2;cy=(max(ys)+min(ys))/2
    scale=.30/span
    points=[(.19+(x-cx)*scale, -.19-(y-cy)*scale) for x,y in clean]
    end=points+[points[0]] if closed else points
    lengths=[math.dist(a,b) for a,b in zip(end,end[1:])]
    if any(length < 1e-14 for length in lengths):
        raise ValueError('存在数值上重合或过近的点，请简化重复点')
    distances=[0.]
    for length in lengths: distances.append(distances[-1]+length)
    total=distances[-1]
    # Sparse polygon corners decelerate. Dense curve samples use arc-length timing.
    ease=len(clean)<=32
    def target(fraction):
        distance=max(0,min(1,fraction))*total
        i=min(len(lengths)-1,bisect.bisect_right(distances,distance)-1)
        v=(distance-distances[i])/lengths[i]
        if ease: v=(1-math.cos(math.pi*v))/2
        a,b=end[i],end[i+1]
        return (a[0]+(b[0]-a[0])*v,a[1]+(b[1]-a[1])*v)
    size=4096
    while True:
        rows=[]
        for i in range(size+1):
            x,y=target(i/size);theta,u=inverse(x,y)
            rows.append([math.tau*i/size,theta,u])
        error=0.
        for i in range(size):
            theta=(rows[i][1]+rows[i+1][1])/2;u=(rows[i][2]+rows[i+1][2])/2
            x,y=target((i+.5)/size)
            error=max(error,math.hypot((1-u)*math.cos(theta)-x,-u*math.sin(theta)-y)*1000)
        if error<=.75: break
        if size>=32768:
            raise ValueError('细节过密，增加精度后误差仍超过0.75像素；请简化点列')
        size*=2
    default={'polygon':str(config.get('sides',''))+'边形','radial-star':str(config.get('tips',''))+'角星','path':'自定义轮廓'}
    return {'rows':rows,'points':points,'closed':closed,'label':config.get('label',default[config['shape']]),
            'fit':{'scale':scale,'input_center':[cx,cy],'target_center':[.19,-.19],
                   'pose_samples':len(rows),'preserves_aspect':True,'safety_box':[.04,.34],
                   'max_midpoint_error_pixels':error,'eased_corners':ease},
            'length':1000,'origin':[700,700]}
