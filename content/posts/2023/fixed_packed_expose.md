---
title: "FixedArr, packed and expose for Yaksha"
summary: "Thinking about FixedArr, packed and expose for Yaksha"
date: 2023-12-27
tags:
  - yaksha
  - idea
---

While working on `FixedArr`, I was thinking what else can be useful for Yaksha. I came up with two ideas.

## New annotation ideas

### Packed
This will compile a `struct` into a packed `struct`. This will be useful for writing binary parsers. `#pragma push(pack, N)` will be used to pack the `struct`. 

I'm also thinking to limit this to only `struct`s and not `class`es. 

```yaksha
@packed("1")
struct Foo:
    a: u8
    b: u16
```

### Expose
This will expose a `struct` / `class` / function to `C`. This will be useful for exposing things to `C` (access from `@native`). `Tuple`s cannot be exposed to `C`. 

```yaksha
@expose("foo") # foo will be the name of the function in `C`
def foo(a: u8, b: u16) -> u32:
    return a + b
```

## `FixedArr`

### Auto casting 

* `FixedArr` and `Array` can be casted to `Ptr`, `AnyPtr` and `AnyPtrToConst`.

### Returning `FixedArr` from functions

Since `FixedArr` is allocated on stack, it is not possible to return it from a function in `C`. However, if we wrap it in a `struct` or `Tuple`, it is possible to return it from a function. 

If we can add few quality of life improvements to `Tuple`, it will be easy to use it as a wrapper for `FixedArr`. 

```yaksha
def foo() -> Tuple[FixedArr[u8, 2]]:
    return tuple(fixedarr(1u8, 2u8))
```

### Impossible assigns (Impossible in `C` should not mean impossible in `Yaksha`)

If we can make fixed arrays and tuples assignable, we can do some interesting things. 

```yaksha
def foo():
    a: FixedArr[u8, 2] = fixedarr(1u8, 2u8)
    b: FixedArr[u8, 2]
    a = b # This is not possible nowS
```
