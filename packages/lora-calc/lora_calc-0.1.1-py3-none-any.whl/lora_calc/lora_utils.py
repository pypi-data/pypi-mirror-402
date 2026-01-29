import math


class LoRaCalculator:
    def __init__(
        self,
        tx_power: int = 20,
        payload_len: int = 7,
        preamble_len: int = 8,
        spreading_factor: int = 6,
        bandwidth: float = 8,
        coding_rate: int = 5,
        crc: bool = False,
        explicit_header: bool = True,
        low_data_rate_opt: bool = True,
    ):
        """
        Initialize the LoRa calculator with given parameters.

        All parameters are validated on initialization and will raise ValueError if invalid.

        Args:
            tx_power (int): Transmit power in dBm. Must be between -14 and 20. Default: 20.
            payload_len (int): Length of the payload in bytes. Must be between 0 and 255. Default: 7.
            preamble_len (int): Length of the preamble in symbols. Must be between 6 and 65535. Default: 8.
            spreading_factor (int): Spreading factor. Must be between 6 and 12 (e.g., 7, 12). Default: 6.
            bandwidth (float): Bandwidth in kHz. Must be one of [7.8, 10.4, 15.6, 20.8, 31.25, 41.7, 62.5, 125, 250, 500]. Default: 8.
            coding_rate (int): Coding rate denominator. Must be one of [5, 6, 7, 8] representing 4/5, 4/6, 4/7, 4/8. Default: 5.
            crc (bool): Whether CRC is enabled. Default: False.
            explicit_header (bool): Whether explicit header is used. Default: True.
            low_data_rate_opt (bool): Whether low data rate optimization is enabled. Default: True.

        Raises:
            ValueError: If any parameter is outside its valid range or not in its allowed set of values.
        """
        if not -14 <= tx_power <= 20:
            raise ValueError(f"tx_power must be between -14 and 20 dBm, got {tx_power}")
        if not 0 <= payload_len <= 255:
            raise ValueError(
                f"payload_len must be between 0 and 255 Bytes, got {payload_len}"
            )
        if not 6 <= preamble_len <= 65535:
            raise ValueError(
                f"preamble_len must be between 6 and 65535 Symbols, got {preamble_len}"
            )
        if not 6 <= spreading_factor <= 12:
            raise ValueError(
                f"spreading_factor must be between 6 and 12, got {spreading_factor}"
            )
        if bandwidth not in [62.5, 125, 250, 500]:
            raise ValueError(
                f"bandwidth must be one of [62.5, 125, 250, 500] kHz, got {bandwidth}"
            )
        if coding_rate not in [5, 6, 7, 8]:
            raise ValueError(
                f"coding_rate must be one of [5, 6, 7, 8] (representing 4/5, 4/6, 4/7, 4/8), got {coding_rate}"
            )

        self.tx_power = tx_power
        self.payload_len = payload_len
        self.preamble_len = preamble_len
        self.spreading_factor = spreading_factor
        self.bandwidth = bandwidth
        self.coding_rate = coding_rate
        self.crc = crc
        self.explicit_header = explicit_header
        self.low_data_rate_opt = low_data_rate_opt

        self.n_preamble_total = self.preamble_len + 4.25

    @property
    def symbol_time(self) -> float:
        """
        Symbol time in milliseconds.
        """
        # 2^SF / BW
        return float(2**self.spreading_factor / self.bandwidth)

    @property
    def symbol_rate(self) -> float:
        """
        Symbol rate in symbols per second.
        """
        # 1000 ms / symbol_time
        return 1000 / self.symbol_time

    @property
    def n_preamble(self) -> int:
        """
        Number of programmable preamble symbols (without overhead).
        """
        return self.preamble_len

    @property
    def t_preamble(self) -> float:
        """
        Time spent on programmable preamble in milliseconds (without sync word overhead).
        This matches the "Preamble Duration" display in Semtech calculator.
        """
        return self.n_preamble * self.symbol_time

    @property
    def t_preamble_total(self) -> float:
        """
        Total preamble time including sync word overhead (4.25 symbols).
        """
        return self.n_preamble_total * self.symbol_time

    @property
    def n_payload(self) -> float:
        """
        Number of payload symbols (with coding overhead).
        Formula from Semtech SX1276/77/78/79 datasheet Section 4.1.1.6.
        """
        # DE (low data rate optimization flag): 1 if enabled, 0 if disabled
        DE = 1 if self.low_data_rate_opt else 0

        # Header flag: 0 if explicit header, 1 if implicit
        IH = 0 if self.explicit_header else 1

        # CRC flag: 1 if enabled, 0 if disabled
        CRC = 1 if self.crc else 0

        # Calculate payload symbol count
        # Formula: 8 + max(ceil((8*PL - 4*SF + 28 + 16*CRC - 20*IH) / (4*(SF-2*DE))) * CR, 0)
        numerator = (
            8 * self.payload_len - 4 * self.spreading_factor + 28 + 16 * CRC - 20 * IH
        )
        denominator = 4 * (self.spreading_factor - 2 * DE)

        payload_symbols = 8 + max(
            math.ceil(numerator / denominator) * self.coding_rate, 0
        )

        return payload_symbols

    @property
    def t_payload(self) -> float:
        """
        Time spent on payload in milliseconds.
        """
        return self.n_payload * self.symbol_time

    @property
    def t_total(self) -> float:
        """
        Total time (ms) including preamble with overhead and payload.
        Matches JavaScript implementation: uses t_preamble_total (with 4.25 overhead).
        """
        return self.t_preamble_total + self.t_payload

    @property
    def throughput(self) -> float:
        """
        Data throughput in bps.
        """
        return (8 * self.payload_len) / self.t_total * 1000

    @property
    def effective_data_rate(self) -> float:
        """
        Effective data rate in bps (theoretical channel capacity).
        Formula: SF * (BW / 2^SF) * (CR_numerator / CR_denominator)
        This represents the maximum theoretical bit rate the modulation can carry,
        ignoring packet overhead like preamble, sync words, and headers.
        """
        # Convert bandwidth from kHz to Hz for calculation, then back to bps
        # CR numerator is (coding_rate - 1), denominator is coding_rate
        # For CR=5 (meaning 4/5), numerator=4, denominator=5

        edr = (
            self.spreading_factor
            * (self.bandwidth * 1000 / (2**self.spreading_factor))
            * (4 / self.coding_rate)
        )
        return float(edr)

    @property
    def link_budget(self) -> float:
        """
        Calculate link budget based on receiver sensitivity.
        Link Budget = Tx Power - Receiver Sensitivity
        """
        # Receiver sensitivity lookup table from SX1276 datasheet (Band 1)
        # Format: {bandwidth: {spreading_factor: sensitivity_dBm}}
        sensitivities = {
            62.5: {6: -121, 7: -126, 8: -129, 9: -132, 10: -135, 11: -137, 12: -139},
            125: {6: -118, 7: -123, 8: -126, 9: -129, 10: -132, 11: -133, 12: -136},
            250: {6: -115, 7: -120, 8: -123, 9: -125, 10: -128, 11: -130, 12: -133},
            500: {6: -111, 7: -116, 8: -119, 9: -122, 10: -125, 11: -128, 12: -130},
        }

        receiver_sensitivity = sensitivities[self.bandwidth][self.spreading_factor]
        return self.tx_power - receiver_sensitivity

    def __repr__(self) -> str:
        return (
            f"LoRaCalculator(SF={self.spreading_factor}, BW={self.bandwidth}, CR=4/{self.coding_rate}, "
            f"payload={self.payload_len}B, preamble={self.preamble_len})"
        )
