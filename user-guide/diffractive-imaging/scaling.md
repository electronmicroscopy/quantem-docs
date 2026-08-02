---
title: Scaling up
---

# Scaling up

:::{note}
Multi-GPU reconstruction and host-memory streaming require a recent version of quantEM. If `device=[0, 1]` or `target_residency` is not accepted, update the package.
:::

Memory requirements grow rapidly with dataset size. A 512 × 512 scan recorded with 96 × 96 detector pixels corresponds to approximately 10 GB of float32 diffraction data, before accounting for the model or optimizer state. This page describes what consumes memory, how to distribute a reconstruction across several GPUs, and how to run one on a cluster.

## What uses GPU memory

Per GPU, with `W` the number of GPUs:

| Term | Size |
| --- | --- |
| Diffraction targets | `(N / W) × Qr × Qc × 4 bytes` |
| Object | `slices × H × W × 8 bytes` |
| Probe | `num_probes × Qr × Qc × 8 bytes` |
| Optimizer state | roughly 2× the tracked parameters |
| Transients | `(batch_size / W) × num_probes × Qr × Qc × 8 bytes`, times a graph factor |

The diffraction targets dominate and are fixed by the data. Everything else scales with your model and batch size.

The point at which an out-of-memory error occurs indicates which term is responsible. A failure on the first iteration, before the forward pass, indicates that the diffraction data itself does not fit, which is addressed by adding GPUs or by streaming from host memory. A failure partway through an iteration indicates that the transient allocations are too large, which is addressed by reducing the batch size.

Binning in reciprocal space is the single most effective reduction, since it reduces the dominant term quadratically. The extent of binning is limited by the probe, because the reciprocal pixel size determines the real-space extent of the probe array, which must contain the probe without wraparound.

## Streaming from host memory

When the diffraction data does not fit in GPU memory, it can be retained in pinned host memory and streamed in batches:

```python
pdset.target_residency = "cpu"
ptycho.reconstruct(num_iters=200, batch_size=128, num_workers=2)
```

We use one to two workers per GPU. The overhead is 5 to 15% per iteration, which is generally a favorable trade for reconstructions that would otherwise not run at all.

## Distributing across multiple GPUs

Multi-GPU reconstruction requires only that a list of device indices be passed to `reconstruct`:

```python
ptycho.reconstruct(num_iters=500, batch_size=128, device=[0, 1, 2, 3])
```

The diffraction patterns are distributed across the GPUs, while the object and probe are replicated on each. Gradients are combined across all GPUs at every step, so that each one continues to hold an identical model.

**The batch size is global rather than per-GPU.** Each GPU processes `batch_size // W` positions, so a given `batch_size` produces the same loss trajectory regardless of how many GPUs are used, and no rescaling of the learning rate is required. We recommend choosing a batch size divisible by the number of GPUs.

Each `reconstruct` call incurs a fixed overhead of roughly ten seconds for process creation and communication setup. Individual calls should therefore perform a substantial amount of work, rather than being issued repeatedly in a loop.

## Preprocessing once and reconstructing many times

Preprocessing is not distributed across GPUs. We therefore perform it once on a single device, save a self-contained file, and reload that file for the reconstruction:

```python
ptycho.preprocess(obj_padding_px=(32, 32))
ptycho.save("preprocessed.zip", mode="o", save_raw_data=True)
```

```python
ptycho = Ptychography.from_file("preprocessed.zip", device="gpu")
ptycho.reconstruct(num_iters=500, device=[0, 1])
```

Setting `save_raw_data=True` embeds the diffraction patterns in the file, which is what allows it to be transferred to another machine.

## Running on a cluster

Batch scripts for HPC systems are provided in the [tutorials repository](https://github.com/electronmicroscopy/quantem-tutorials/tree/main/tutorials/diffractive_imaging/hpc), covering an interactive `salloc` launch, a SLURM batch job, and a multi-node run.

When launched under `torchrun`, quantEM detects the `RANK`, `LOCAL_RANK`, and `WORLD_SIZE` environment variables, binds each rank to its local GPU, and does not spawn processes of its own. The reconstruction script is otherwise unchanged, except that the save must be guarded so that only rank 0 writes:

```python
if rank == 0:
    ptycho.save(output_path, mode="o")
dist.barrier()
dist.destroy_process_group()
```

The example script reads its configuration from environment variables, which allows a single script to be reused across many jobs.

:::{seealso}
[Multi-GPU reconstructions](https://github.com/electronmicroscopy/quantem-tutorials/blob/main/tutorials/diffractive_imaging/ptycho_iter_08_multi_gpu.ipynb) in the tutorials repository compares single-GPU and multi-GPU runs directly, and works through the memory budgeting described above.
:::
