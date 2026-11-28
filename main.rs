cprintf fn(fmt: StaticCStr, item: UInt32) {
    // Code injected here
}

// processNumbers fn(foodGood: Bool, modifier: UInt32) UInt32 {
//     driveGood: Bool = true
//     lifeGood: = foodGood and driveGood

//     1000

//     val: UInt32 = 1
//     val = 10

//     doIf: = lifeGood
//     if doIf {
//         val = 40
//     } else {
//         val = 30
//     }
//     val = val / 10

//     val2: UInt32 = 4000 + 100
//     val2 = val2 - 1000
//     val3: = val + val2
//     val3 = val3 * 10
//     cprintf(c"Pre Result: %d\n", val3)
//     val3 = val3 * modifier

//     return val3
// }

// alignment: 4 bytes
// size: 12 bytes
Triple struct{
    a: UInt32
    b: UInt32
    c: Bool
}

main fn() {

    //result: = processNumbers(false, 2)

    cprintf(c"Hello World\n", 0)


    triple: = Triple{
        b .= 999
        c .= true
        a .= 20
    }

    cprintf(c"a: %d\n", triple.a)
    cprintf(c"b: %d\n", triple.b)

    if triple.c {
        cprintf(c"c: true", 0)
    } else {
        cprintf(c"c: false", 0)
    }

}