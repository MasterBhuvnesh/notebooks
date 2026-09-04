## Question 1

Find the **network address** of the host with IP address:

```text
168.14.32.12
```

Assume the default classful mask.

---

## Question 2

Find the **subnetwork address** for:

```text
IP Address = 200.45.34.56
Subnet Mask = 255.255.240.0
```

using the straight binary method.

---

## Question 3

Find the **subnetwork address** for:

```text
IP Address = 19.30.84.5
Subnet Mask = 255.255.192.0
```

using the shortcut method.

---

## Question 4

A router receives a packet with destination address:

```text
190.240.224.33
```

Find the subnetwork address if the subnet mask is:

```text
/19
```

---

## Question 5

A router receives a packet with the destination address:

```text
190.240.33.91
```

Show how the router finds the **network address** and **subnetwork address** assuming the subnet mask is:

```text
/19
```

---

## Question 6

A company is granted the Class C address:

```text
201.70.64.0
```

The company requires **6 subnets**.

Design the subnet mask and determine:

* Borrowed bits
* Number of subnets
* Hosts per subnet
* Network addresses
* Broadcast addresses
* Valid host ranges

---

## Question 7

A company is granted the Class B address:

```text
181.56.0.0
```

The company requires:

```text
1000 subnets
```

Determine:

* Borrowed bits
* New subnet mask
* Prefix length
* Number of subnets
* Number of hosts per subnet

---

## Question 8

An organisation is granted the block:

```text
130.56.0.0/16
```

The administrator requires:

```text
1024 subnets
```

Find:

* Number of addresses in each subnet
* Subnet prefix
* First and last address of the first subnet
* First and last address of the last subnet

---

## Question 9

A small organisation is given the block:

```text
205.16.37.24/29
```

Find:

* First address
* Last address
* Number of addresses in the block

using both the binary method and the shortcut method.

---

## Question 10

One address in a block is:

```text
167.199.170.82/27
```

Find the network address.

---

## Question 11

One address in a block is:

```text
205.16.37.39/28
```

Find:

* First address
* Last address
* Total addresses
* Usable host range

using:

* Binary method
* Mask method

---

## Question 12

Each of the following addresses belongs to a block.

Find the **first address**, **last address**, and **usable host range**.

### (a)

```text
14.12.72.8/24
```

### (b)

```text
200.107.16.17/18
```

### (c)

```text
70.110.19.17/16
```

---

## Question 13

An organisation is granted the block:

```text
130.34.12.64/26
```

The organisation requires:

```text
4 subnets
```

Design the subnets and show the address range of each subnet.

---

## Question 14

An organisation is granted the block:

```text
14.24.74.0/24
```

The organisation needs three sub-blocks:

* One of 120 addresses
* One of 60 addresses
* One of 10 addresses

Design the VLSM allocation.

---

## Question 15

An organisation is granted the block:

```text
14.24.74.0/24
```

The organisation needs three sub-blocks:

* One of 10 addresses
* One of 60 addresses
* One of 120 addresses

Design the VLSM allocation.

---

## Question 16

An ISP is granted the block:

```text
190.100.0.0/16
```

The ISP must serve:

* 64 customers requiring 256 addresses each
* 128 customers requiring 128 addresses each
* 128 customers requiring 64 addresses each

Determine:

* Prefix used for each group
* Address ranges allocated
* Total addresses used
* Remaining addresses available

---

## Question 17

An ISP is granted the block:

```text
16.12.64.0/20
```

The ISP must allocate addresses to:

```text
8 organisations
```

Each organisation requires:

```text
256 addresses
```

Find:

* Number and range of addresses in the ISP block
* Range allocated to each organisation
* Unallocated range
* Distribution outline

---

## Question 18

An ISP is granted the block:

```text
80.70.56.0/21
```

The ISP must allocate addresses to:

* Two organisations requiring 500 addresses each
* Two organisations requiring 250 addresses each
* Three organisations requiring 50 addresses each

Find:

* Number and range of addresses in the ISP block
* Address allocation for each organisation
* Unallocated range
* Distribution outline

---

## Question 19

A supernet has:

```text
First Address = 205.16.32.0
Mask = 255.255.248.0
```

A router receives packets destined for:

```text
205.16.37.44
205.16.42.56
205.17.33.76
```

Determine which packets belong to the supernet.

---

## Question 20

A supernet has:

```text
First Address = 205.16.32.0
Mask = 255.255.248.0
```

Find:

* Prefix length
* Number of Class C blocks aggregated
* First address
* Last address
* Total addresses

---

## Question 21

A company needs approximately:

```text
600 addresses
```

Determine whether each of the following sets of Class C blocks can form a valid supernet.

### (a)

```text
198.47.32.0
198.47.33.0
198.47.34.0
```

### (b)

```text
198.47.32.0
198.47.42.0
198.47.52.0
198.47.62.0
```

### (c)

```text
198.47.31.0
198.47.32.0
198.47.33.0
198.47.52.0
```

### (d)

```text
198.47.32.0
198.47.33.0
198.47.34.0
198.47.35.0
```

For each case determine whether a valid supernet can be formed and explain why.

---

## Question 22

Determine the supernet mask required to aggregate:

```text
16 contiguous Class C networks
```

Show:

* Binary calculation
* Prefix length
* Decimal mask


