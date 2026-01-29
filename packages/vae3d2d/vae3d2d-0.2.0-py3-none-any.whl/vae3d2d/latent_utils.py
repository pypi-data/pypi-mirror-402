import torch

@torch.no_grad()
def compute_latent_channel_stats(encoder, dataloader, device, max_batches=None, use_amp=False):
    sum_c = None
    sumsq_c = None
    n_total = 0  # number of elements per channel accumulated

    for b, batch in enumerate(dataloader):
        if max_batches is not None and b >= max_batches:
            break

        x = batch[0] if isinstance(batch, (tuple, list)) else batch  # adapt if your batch is (x, meta)
        x = x.to(device)
        if use_amp:
            with torch.amp.autocast():
                z = encoder(x)[0]  # (B, C, D, H, W)  or (B, C, ...)
        else:
            z = encoder(x)[0]  # (B, C, D, H, W)  or (B, C, ...)
        B, C = z.shape[:2]
        z_flat = z.permute(1, 0, *range(2, z.ndim)).contiguous().view(C, -1)  # (C, N)

        if sum_c is None:
            sum_c = torch.zeros(C, device=device, dtype=torch.float64)
            sumsq_c = torch.zeros(C, device=device, dtype=torch.float64)

        sum_c += z_flat.double().sum(dim=1)
        sumsq_c += (z_flat.double() ** 2).sum(dim=1)
        n_total += z_flat.shape[1]

    mean_c = (sum_c / n_total).float()                       # (C,)
    var_c = (sumsq_c / n_total - mean_c.double()**2).clamp_min(1e-12).float()
    std_c = torch.sqrt(var_c)

    return mean_c, std_c


@torch.no_grad()
def sample_from_channel_gaussian_and_decode(decoder, mean_c, std_c, shape, device, n=4, use_amp=False):
    """
    shape: (B, C, D, H, W) to sample. Use your latent shape.
    mean_c/std_c: (C,)
    """

    B, C, *spatial = shape

    mean = mean_c.view(1, C, *([1] * len(spatial))).to(device)
    std  = std_c.view(1, C, *([1] * len(spatial))).to(device)

    eps = torch.randn(n, C, *spatial, device=device)
    z = mean + std * eps
    if use_amp:
        with torch.amp.autocast():
            x_hat = decoder(z)
    else:
        x_hat = decoder(z)
    return z, x_hat