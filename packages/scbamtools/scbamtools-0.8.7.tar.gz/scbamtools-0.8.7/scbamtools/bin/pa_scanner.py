from scbamtools.gene_model import *

genome = IndexedFasta("/data/rajewsky/genomes/GRCh38/GRCh38.fa")

w = 30
thresh = 0.6 * w
d = 50  # distance that is considered "close" to priming site
for chrom, size in genome.chrom_sizes.items():
    for pos in range(size - w):
        seq = genome.get_data(chrom, pos, pos + w, "+").upper()

        As = seq.count("A")
        Ts = seq.count("T")

        if As >= thresh and seq.startswith("AAA"):
            print(f"{chrom}\t{pos - d}\t{pos}\t{100*As/w:.0f}\t+\t{seq}")

        if Ts >= thresh and seq.endswith("TTT"):
            print(f"{chrom}\t{pos}\t{pos + d}\t{100*Ts/w:.0f}\t-\t{seq}")
