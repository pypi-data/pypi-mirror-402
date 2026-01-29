# CaseMaster-Py 🛠️

Mətnləri proqramlaşdırma formatlarına çevirmək üçün sürətli alət.

## İstifadə
```python
from casemaster import CaseMaster

cm = CaseMaster()
print(cm.to_snake("Salam Dunya")) # salam_dunya
print(cm.to_camel("user_login_count")) # userLoginCount