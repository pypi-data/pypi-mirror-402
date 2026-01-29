#include <torch/extension.h>

template <typename scalar_t>
__global__ void sparse_to_dense_kernel(
    const int64_t* __restrict__ index,
    const scalar_t* __restrict__ value,
    scalar_t* __restrict__ out,
    const int64_t m,
    const int64_t n,
    const int64_t nnz) {
  const int64_t i = blockIdx.x * blockDim.x + threadIdx.x;
  if (i < nnz) {
    const int64_t r = index[i];
    const int64_t c = index[nnz + i];
    if (r >= 0 && r < m && c >= 0 && c < n) {
      out[r * n + c] = value[i];  // row-major for torch.linalg
    }
  }
}

template <typename scalar_t>
void sparse_to_dense_cuda_impl(
    const torch::Tensor& index,
    const torch::Tensor& value,
    torch::Tensor& out,
    int64_t m,
    int64_t n) {
  const int64_t nnz = index.size(1);
  if (nnz == 0) {
    out.zero_();
    return;
  }
  const int64_t* d_index = index.data_ptr<int64_t>();
  const scalar_t* d_value = value.data_ptr<scalar_t>();
  scalar_t* d_out = out.data_ptr<scalar_t>();
  int block = 256;
  int grid = (int)((nnz + block - 1) / block);
  sparse_to_dense_kernel<scalar_t><<<grid, block>>>(d_index, d_value, d_out, m, n, nnz);
}

void sparse_to_dense_cuda(
    const torch::Tensor& index,
    const torch::Tensor& value,
    torch::Tensor& out,
    int64_t m,
    int64_t n) {
  TORCH_CHECK(index.is_cuda() && value.is_cuda() && out.is_cuda());
  TORCH_CHECK(index.dim() == 2 && index.size(0) == 2);
  TORCH_CHECK(value.dim() == 1 && value.size(0) == index.size(1));
  TORCH_CHECK(out.dim() == 2 && out.size(0) == m && out.size(1) == n);
  out.zero_();
  if (value.scalar_type() == torch::kFloat32) {
    sparse_to_dense_cuda_impl<float>(index, value, out, m, n);
  } else if (value.scalar_type() == torch::kFloat64) {
    sparse_to_dense_cuda_impl<double>(index, value, out, m, n);
  } else {
    TORCH_CHECK(false, "value must be float32 or float64");
  }
}

PYBIND11_MODULE(_sparse_to_dense, m) {
  m.def("sparse_to_dense", &sparse_to_dense_cuda, "COO to dense (column-major) on GPU");
}
