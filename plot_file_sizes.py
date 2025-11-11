#!/usr/bin/env python3
"""
Create a histogram of file sizes for indexed ISMIP6 files.
"""

import numpy as np
import matplotlib.pyplot as plt
from ismip6_helper import get_file_index


def format_bytes(size_bytes):
    """Convert bytes to human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def main():
    print("Loading file index...")
    df = get_file_index()

    print(f"Total files: {len(df)}")
    print(f"\nFile size statistics:")
    print(f"  Min:    {format_bytes(df['size_bytes'].min())}")
    print(f"  Max:    {format_bytes(df['size_bytes'].max())}")
    print(f"  Mean:   {format_bytes(df['size_bytes'].mean())}")
    print(f"  Median: {format_bytes(df['size_bytes'].median())}")
    print(f"  Total:  {format_bytes(df['size_bytes'].sum())}")

    # Convert to MB for easier visualization
    sizes_mb = df['size_bytes'] / (1024 * 1024)

    # Create histogram
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

    # Linear scale histogram
    ax1.hist(sizes_mb, bins=50, edgecolor='black', alpha=0.7)
    ax1.set_xlabel('File Size (MB)')
    ax1.set_ylabel('Number of Files')
    ax1.set_title('ISMIP6 File Size Distribution (Linear Scale)')
    ax1.grid(True, alpha=0.3)

    # Log scale histogram
    # Filter out zeros for log scale
    sizes_mb_nonzero = sizes_mb[sizes_mb > 0]
    ax2.hist(sizes_mb_nonzero, bins=50, edgecolor='black', alpha=0.7)
    ax2.set_xlabel('File Size (MB)')
    ax2.set_ylabel('Number of Files')
    ax2.set_title('ISMIP6 File Size Distribution (Log Scale)')
    ax2.set_yscale('log')
    ax2.grid(True, alpha=0.3, which='both')

    plt.tight_layout()
    plt.savefig('ismip6_file_sizes.png', dpi=150, bbox_inches='tight')
    print(f"\nHistogram saved to: ismip6_file_sizes.png")

    # Print size distribution by percentiles
    print(f"\nFile size percentiles:")
    for percentile in [10, 25, 50, 75, 90, 95, 99]:
        value = np.percentile(df['size_bytes'], percentile)
        print(f"  {percentile:2d}th: {format_bytes(value)}")

    # Show distribution by variable
    print(f"\nMean file size by variable (top 10 largest):")
    var_sizes = df.groupby('variable')['size_bytes'].agg(['mean', 'count']).sort_values('mean', ascending=False)
    for var, row in var_sizes.head(10).iterrows():
        print(f"  {var:<30s} {format_bytes(row['mean']):>12s}  ({int(row['count'])} files)")

    print(f"\nMean file size by variable (top 10 smallest):")
    for var, row in var_sizes.tail(10).iterrows():
        print(f"  {var:<30s} {format_bytes(row['mean']):>12s}  ({int(row['count'])} files)")


if __name__ == "__main__":
    main()
