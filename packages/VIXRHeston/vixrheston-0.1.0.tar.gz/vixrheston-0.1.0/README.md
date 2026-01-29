# VIXRHeston

A small Python package for computing the squared VIX (VIX²) under a (rough) Heston-type setup.

## Installation

### From PyPI
```bash
pip install VIXRHeston
```

## Quick start

```python
import numpy as np
from VIXRHeston import vec_c, vec_x
from VIXRHeston import squared_VIX

H,n = 0.1,2
alpha, rn= H+0.5, 1+10*(1/(n)**0.9)
c, x = vec_c(n,rn,alpha), vec_x(n,rn,alpha)
t, tau = 0, 1/12
rho, lamb,theta,nu,V0 = -0.7,0.1,0.03,0.3, 0.01
VIX2 = squared_VIX(t, c, x, V0,lamb,theta,nu,rho, tau)
VIX  = np.sqrt(VIX2)
print(VIX)
```

## License
MIT License. See `LICENSE`.