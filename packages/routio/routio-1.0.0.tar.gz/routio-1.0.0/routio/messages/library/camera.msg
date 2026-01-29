

message CameraIntrinsics {
    int width;
    int height;
    tensor intrinsics<3, 3>;
    tensor distortion; 
} 

message CameraExtrinsics {
    Header header;
    tensor rotation<3, 3>;
    tensor translation<1, 3>;
}

message Frame {
    Header header;
    tensor image;
}