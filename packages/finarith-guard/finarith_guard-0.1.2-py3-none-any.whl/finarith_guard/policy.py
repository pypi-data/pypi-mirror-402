class GuardPolicy:

    # thresholds
    MAX_REL_ERROR = 1e-12
    MAX_ABS_ERROR = 1e-9 #Accepts IEEE float noise

    # rules
    DISALLOW_FLOAT_FOR_MONEY = True
    DISALLOW_MIXED_TYPES = True

    # action
    RAISE_ON_VIOLATION = False   # True for prod, False for dev
