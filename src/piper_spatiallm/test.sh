huggingface-cli download manycore-research/SpatialLM-Testset pcd/scene0000_00.ply --repo-type dataset --local-dir .
python inference.py --point_cloud pcd/scene0000_00.ply --output scene0000_00.txt --model_path manycore-research/SpatialLM-Llama-1B
python visualize.py --point_cloud pcd/scene0000_00.ply --layout scene0000_00.txt --save scene0000_00.rrd
rerun scene0000_00.rrd
