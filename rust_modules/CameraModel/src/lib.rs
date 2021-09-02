//TODO(hayley): return a result for falliable calls
#[derive(Copy,Clone,Debug)]
pub enum CaptureMode{
    Continous,
    SingleShot,
    Burst
}
#[derive(Copy,Clone,Debug)]
pub enum PixelFormat{
    MonoU16,
    MonoU8,
}

#[derive(Copy,Clone,Debug)]
pub enum Pixels<'a>{
    MonoU16(&'a [u16]),
    MonoU8(&'a [u8]),
}

pub trait Frame{
    fn format(&self) -> PixelFormat;
    fn size(&self) -> (usize, usize);
    fn pixels<'a>(&'a self) -> Pixels<'a>;
}

pub trait Camera{
    type Frame : Frame + ?Sized;
    fn new() -> Self;
    fn set_exposure(&mut self, exposure : std::time::Duration);
    fn get_exposure(&self) -> std::time::Duration;
    fn set_region_of_interest(&mut self, x : (usize, usize), y: (usize, usize));
    fn get_region_of_interest(&self) -> ((usize, usize), (usize, usize));
    fn set_capture_mode(&mut self, mode : CaptureMode);
    fn get_capture_mode(&self) -> CaptureMode;
    fn snap(&mut self) -> &Self::Frame;
}

