cprintf fn(fmt: StaticCStr, item: UInt32) {
    // Code injected here
}

processNumbers fn(foodGood: Bool, modifier: UInt32) UInt32 {
    driveGood: Bool = true
    lifeGood: = foodGood and driveGood

    1000

    val: UInt32 = 1
    val = 10

    doIf: = lifeGood
    if doIf {
        val = 40
    } else {
        val = 30
    }
    val = val / 10

    val2: UInt32 = 4000 + 100
    val2 = val2 - 1000
    val3: = val + val2
    val3 = val3 * 10
    cprintf(c"Pre Result: %d\n", val3)
    val3 = val3 * modifier

    return val3
}

main fn() {
    result: = processNumbers(false, 2)

    cprintf(c"Hello World\n", 0)
    cprintf(c"Result: %d\n", result)
}