"""Unit tests for quantized model transfer calculations in EdgeSimPy NetworkFlow."""

import unittest

from edge_sim_py.components.network_flow import NetworkFlow


class TestQuantizedNetworkFlow(unittest.TestCase):
    def test_calculate_model_transfer_size(self):
        num_params = 10000

        fp32_size = NetworkFlow.calculate_model_transfer_size(num_params, nbits=32)
        self.assertEqual(fp32_size, 40000)

        fp16_size = NetworkFlow.calculate_model_transfer_size(num_params, nbits=16)
        self.assertEqual(fp16_size, 20000)

        int8_size = NetworkFlow.calculate_model_transfer_size(num_params, nbits=8, block_size=64)
        num_blocks = (num_params + 63) // 64
        expected_int8 = num_params + (num_blocks * 4)
        self.assertEqual(int8_size, expected_int8)

        int4_size = NetworkFlow.calculate_model_transfer_size(num_params, nbits=4, block_size=64)
        expected_int4 = ((num_params + 1) // 2) + (num_blocks * 4)
        self.assertEqual(int4_size, expected_int4)

        ratio = fp32_size / int4_size
        self.assertGreater(ratio, 7.0)

    def test_invalid_nbits(self):
        with self.assertRaises(ValueError):
            NetworkFlow.calculate_model_transfer_size(1000, nbits=3)

    def test_apply_model_quantization(self):
        flow = NetworkFlow.__new__(NetworkFlow)
        flow.metadata = {}

        quantized_bytes = flow.apply_model_quantization(num_parameters=6400, nbits=4, block_size=64)

        self.assertEqual(flow.data_to_transfer, quantized_bytes)
        self.assertEqual(flow.metadata["type"], "model_update")
        self.assertEqual(flow.metadata["nbits"], 4)
        self.assertEqual(flow.metadata["num_parameters"], 6400)
        self.assertGreater(flow.metadata["compression_ratio"], 7.0)


if __name__ == "__main__":
    unittest.main()
