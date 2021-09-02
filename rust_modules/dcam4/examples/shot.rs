use dcam4::*;
use CameraModel::{Camera, Frame};
fn main() {
    let mut cam = DcamCamera::new();
    let shot = cam.snap();
    // println!("shot = {:?}", shot);
    println!("pixels = {:?}", shot.pixels());
    println!("sum = {}", match shot.pixels() {
        CameraModel::Pixels::MonoU16(x) => {x.into_iter().map(|&x| x as usize).sum::<usize>()},
        CameraModel::Pixels::MonoU8(x) => {x.into_iter().map(|&x| x as usize).sum::<usize>()}
    });
}



