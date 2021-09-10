use pyo3::prelude::*;
use pyo3::exceptions;
use mcl_stagedrive::microdrive;
use mcl_stagedrive::madlib;
#[pyclass(name="XyStage")]
struct PyXyStage {
    dev : microdrive::Device,
}

#[pyclass(name="XyzStage")]
struct PyXyzStage {
    xy : PyXyStage,
    z : madlib::Device,
}

struct Wrapper<T>(T);

impl<T : std::fmt::Debug> std::convert::From<Wrapper<T>> for PyErr{
    fn from(e: Wrapper<T>) -> PyErr {
        exceptions::PyException::new_err(format!("{:?}",e.0))
    }
}

fn to_py_err<T,  E : std::fmt::Debug>(original : Result<T,E>) -> PyResult<T> {
    original.map_err(|e| PyErr::from(Wrapper(e)))
}

#[pymethods]
impl PyXyStage {
    #[new]
    pub fn new() -> PyResult<Self> {
        Ok(Self{
            dev : microdrive::get_all_devices().pop().ok_or(exceptions::PyValueError::new_err("No free madcitylabs microdrive found. Is another program holding the handle?"))?
        })
    }
    pub fn move_xy(&self, distance : [f64;2], velocity : [f64;2]) ->   PyResult<()> {
        to_py_err(self.dev.move_two_axis((microdrive::Axis::M2,microdrive::Axis::M1), (velocity[0], velocity[1]), (distance[0], distance[1])))
    }
    pub fn move_x(&self, distance : f64, velocity : f64) ->   PyResult<()> {
        to_py_err(self.dev.move_single_axis(microdrive::Axis::M2, velocity, distance))
    }
    pub fn move_y(&self, distance : f64, velocity : f64) ->   PyResult<()> {
        to_py_err(self.dev.move_single_axis(microdrive::Axis::M1, velocity, distance))
    }
    pub fn supported_velocity_range(&mut self) -> PyResult<[f64;2]> {
        let info = to_py_err(self.dev.get_info())?;
        let min_velocity = info.min_velocity();
        let max_velocity = *([info.max_velocity_one_axis(), info.max_velocity_two_axis()].iter().min_by(|a, b| b.partial_cmp(a).unwrap()).unwrap());
        Ok([min_velocity, max_velocity])
    }
}

#[pymethods]
impl PyXyzStage {
    #[new]
    pub fn new() -> PyResult<Self> {
        Ok(Self{
            xy : PyXyStage::new()?,
            z : madlib::get_all_devices().pop().ok_or(exceptions::PyValueError::new_err("No free madcitylabs nanodrive found. Is another program holding the handle?"))?
        })
    }
    pub fn move_xy(&self, distance : [f64;2], velocity : [f64;2]) ->   PyResult<()> {
        self.xy.move_xy(distance, velocity)
    }
    pub fn move_x(&self, distance : f64, velocity : f64) ->   PyResult<()> {
        self.xy.move_x(distance, velocity)
    }
    pub fn move_y(&self, distance : f64, velocity : f64) ->   PyResult<()> {
        self.xy.move_y(distance, velocity)
    }
    pub fn supported_velocity_range(&mut self) -> PyResult<[f64;2]> {
        self.xy.supported_velocity_range()
    }

    #[getter]
    pub fn get_z(&self) -> PyResult<f64> {
        to_py_err(self.z.read_position_z())
    }

    #[setter]
    pub fn set_z(&mut self, position_in_microns : f64) -> PyResult<()> {
        to_py_err(self.z.move_to_z(position_in_microns))
    }
}


#[pymodule]
fn _pynta_drivers(py: Python, m: &PyModule) -> PyResult<()> {
    // m.add_function(wrap_pyfunction!(double, m)?)?;
    m.add_class::<PyXyStage>()?;
    m.add_class::<PyXyzStage>()?;
    Ok(())
}
