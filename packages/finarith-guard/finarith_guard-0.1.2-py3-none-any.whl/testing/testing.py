from finarith_guard import SafeFloat, GuardPolicy

print("\nTESTING finarith-guard FROM TestPyPI")

print("Version check:")
import finarith_guard
print(finarith_guard.__version__)

print("\nFloating precision detection test:")

GuardPolicy.RAISE_ON_VIOLATION = True

a = SafeFloat(1e20)
b = SafeFloat(1)

print(a + b)

print("\nStrict mode test:")

GuardPolicy.RAISE_ON_VIOLATION = True

try:
    SafeFloat(0.1) + SafeFloat(0.2)
    print("FAIL: exception not raised")

except Exception as e:
    print("PASS: exception raised")
    print(e)


print(GuardPolicy.MAX_REL_ERROR, GuardPolicy.MAX_ABS_ERROR)

import inspect

# print(inspect.getsource(SafeFloat.__add__))

a = SafeFloat(1e18)
b = SafeFloat(0.01)

print(a + b)



total = SafeFloat(0)

for i in range(1000000):

    total = total + SafeFloat(0.01)

    if i % 10000 == 0:
        SafeFloat(total.unwrap()) + SafeFloat(0)
