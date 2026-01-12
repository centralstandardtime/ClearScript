// RAW block example > direct StateScript injection
int count = 0;
int randomValue = 0;

raw {
    SHUFFLE Output 12345 Red Blue Green Yellow
    GUID RandomID
    LERP 0 100 0.5 MidPoint
}

function processData() {
    count++;
    randomValue = count * 2;
}

label: start
    processData();
    
    raw {
        WAITHEARTBEAT DeltaTime
        ALLOCARRAY TempVars 5
    }
    
    if (count < 10) {
        goto start;
    }
    
    kill();
