# lora-calc

A Python library for calculating LoRa (Long Range) wireless transmission parameters. Compute symbol times, airtime, throughput, and link budgets based on LoRa configuration settings.

## Installation

```bash
pip install lora-calc
```

Or with Poetry:

```bash
poetry add lora-calc
```

## Usage

```python
from lora_calc import LoRaCalculator

# Create a calculator with your LoRa parameters
calc = LoRaCalculator(
    tx_power=20,              # Transmit power in dBm (-14 to 20)
    payload_len=125,          # Payload length in bytes (0-255)
    preamble_len=8,           # Preamble length in symbols (6-65535)
    spreading_factor=10,      # SF6-SF12
    bandwidth=125,            # 62.5, 125, 250, or 500 kHz
    coding_rate=5,            # 5, 6, 7, or 8 (representing 4/5, 4/6, 4/7, 4/8)
    crc=True,                 # Enable CRC
    explicit_header=True,     # Use explicit header mode
    low_data_rate_opt=True,   # Low data rate optimization
)

# Get transmission parameters
print(f"Symbol time: {calc.symbol_time} ms")
print(f"Symbol rate: {calc.symbol_rate} symbols/sec")
print(f"Preamble duration: {calc.t_preamble} ms")
print(f"Payload duration: {calc.t_payload} ms")
print(f"Total airtime: {calc.t_total} ms")
print(f"Throughput: {calc.throughput} bps")
print(f"Effective data rate: {calc.effective_data_rate} bps")
print(f"Link budget: {calc.link_budget} dB")
```

## Parameters

| Parameter           | Range                   | Description                                   |
| ------------------- | ----------------------- | --------------------------------------------- |
| `tx_power`          | -14 to 20 dBm           | Transmit power                                |
| `payload_len`       | 0-255 bytes             | Payload length                                |
| `preamble_len`      | 6-65535 symbols         | Preamble length                               |
| `spreading_factor`  | 6-12                    | LoRa spreading factor                         |
| `bandwidth`         | 62.5, 125, 250, 500 kHz | Signal bandwidth                              |
| `coding_rate`       | 5, 6, 7, 8              | Forward error correction (4/5, 4/6, 4/7, 4/8) |
| `crc`               | True/False              | Enable CRC check                              |
| `explicit_header`   | True/False              | Use explicit header mode                      |
| `low_data_rate_opt` | True/False              | Low data rate optimization                    |

## Calculated Properties

| Property              | Unit        | Description                                      |
| --------------------- | ----------- | ------------------------------------------------ |
| `symbol_time`         | ms          | Duration of one symbol                           |
| `symbol_rate`         | symbols/sec | Symbols transmitted per second                   |
| `t_preamble`          | ms          | Preamble duration (programmable symbols only)    |
| `t_preamble_total`    | ms          | Total preamble including sync word overhead      |
| `n_payload`           | symbols     | Number of payload symbols                        |
| `t_payload`           | ms          | Payload transmission time                        |
| `t_total`             | ms          | Total time on air                                |
| `throughput`          | bps         | Actual data throughput                           |
| `effective_data_rate` | bps         | Theoretical channel capacity                     |
| `link_budget`         | dB          | Link budget based on SX1276 receiver sensitivity |

## References

- [SX1276 Data Sheet](https://www.semtech.com/products/wireless-rf/lora-connect/sx1276)
- [LoRa Theory](https://doi.org/10.3390/s16091466)
- [Official LoRa Calculator](https://www.semtech.com/design-support/lora-calculator)

### Other LoRa Calculator Implementations

- [lora-air-time](https://github.com/ifTNT/lora-air-time)
- [lorawan_toa](https://github.com/tanupoo/lorawan_toa)
- [airtime-calculator](https://github.com/avbentem/airtime-calculator)
