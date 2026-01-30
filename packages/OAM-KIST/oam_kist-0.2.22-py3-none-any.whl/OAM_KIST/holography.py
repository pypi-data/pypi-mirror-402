import os

import numpy as np
import cv2
from scipy.special import factorial, eval_genlaguerre

from .utils import inv_sinc, inv_sinc_minus, diffraction


def generate_oam_superposition(res, pixel_pitch, beam_w0, l_modes, p_modes, weights, prepare=True, measure=False):
    """ Creat E field of superimposed OAM mode (Interferogram method)

    Args:
        res (list[int]): resolution of SLM. [x resolution, y resolution]
        pixel_pitch (float): pixel size. specified at device document
        beam_w0 (float): beam-waist at z=0.
        l_modes (list[int]): selected l indices for superposion. list with length 1 for eigen mode
        p_modes (list[int]): selected p indices for superposion. list with length 1 for eigen mode
        weights (list[float]): weights for selected l modes.
        prepare (bool): whether to prepare the OAM superposition before generating superposition
        measure (bool): whether to measure the OAM superposition before generating superposition

    Returns:
        np.ndarray[float], np.ndarray[float], np.ndarray[float], np.ndarray[float]: information about E field and meshgrid i.e. superimosed

    Example:
        >>> import numpy as np
        >>> slm_res = [1920, 1080]
        >>> slm_pitch = 8e-1
        >>> input_w0 = 0.8e-3
        >>> target_l = [-3, -1, 1, 3]
        >>> target_p = np.zeros_like(target_l)
        >>> target_weights = [0.4, 0.03, 0.07, 0.5]
        >>> superposition_args = [slm_res, slm_pitch, input_w0, target_l, target_p, target_weights, True, False]
        >>> fields = generate_oam_superposition(*superposition_args)
    """
    x = np.linspace(-res[0] * pixel_pitch / 2, res[0] * pixel_pitch / 2, res[0])
    y = np.linspace(-res[1] * pixel_pitch / 2, res[1] * pixel_pitch / 2, res[1])
    X, Y = np.meshgrid(x, y)

    R = np.sqrt(X ** 2 + Y ** 2)
    Phi = np.arctan2(Y, X)

    R[R == 0] = 1e-10

    E_total = np.zeros_like(Phi, dtype=complex)
    for l, p, w in zip(l_modes, p_modes, weights):
        C = np.sqrt(2 * factorial(p)/(np.pi*factorial(np.abs(l))))
        E_total += w * C * ((np.sqrt(2) * R / beam_w0) ** abs(l)) * eval_genlaguerre(p,abs(l),2*((R**2)/(beam_w0**2))) * np.exp(-(R**2) / (beam_w0**2)) * np.exp(-1j * l * Phi)

    if prepare:
        E_total = E_total
    elif measure:
        E_total = E_total.conjugate()
    else: return 0

    Amp = np.abs(E_total)
    Phase = np.angle(E_total) + np.pi

    return Amp, Phase, X, Y


def encode_hologram(Amp, Phase, X, Y, pixel_pitch, d, N_steps=0, M=1, prepare=False, measure=False, save=False, path="", name="", use_inv_sinc_minus=False):
    """phase mask for given amplitude and phase map of superimposed OAM mode.

    입력받은 위상, 진폭 정보를 논문 공식에 대입하여 이 상태를 인코딩하는 SLM 홀로그램을 생성합니다.
    Fundamental Gaussian 모드와의 분리를 위해서 간격이 d 픽셀인 그레이팅이 적용됩니다.
    상태 준비에 사용될지, 측정에 사용될지에 따라서 그레이팅의 방향이 바뀝니다. 변수 parity가 이것을 반영합니다.
    생성된 홀로그램을 저장할 수 있습니다.

    Args:
        Amp (np.ndarray[float]): amplitude map of superimposed OAM mode. 0. <= *Amp <= 1.
        Phase (np.ndarray[float]): phase map of superimposed OAM mode. -pi < *Phase <= pi
        X (np.ndarray[float]): x dependent meshgrid.
        Y (np.ndarray[float]): y dependent meshgrid.
        pixel_pitch (float): pixel size. specified at device document
        d (float): grating width. dimension in # of pixel
        N_steps (float): number of steps per grating with period d. N_steps=0 is equal to N_steps=d (continuous)
        M (int): phase depth. M is basically 1
        prepare (bool): decide whether to prepare.
        measure (bool): decide whether to measure.
        save (bool): decide whether to save.
        path (string): directory path for images. needed only when arg save is True
        name (string): filename of this image. needed only when arg save is True
        use_inv_sinc_minus (bool): whether to use inverse sinc in domain [-pi,0] or not.

    Return:
        np.ndarray[float] or None: returns carculated hologram.
        if arg save is False(default), a hologram in numpy ndarray. And if not, hologram is saved in the directory addording to arg path.

    Example:
        >>> import numpy as np
        >>> slm_res = [1920, 1080]
        >>> slm_pitch = 8e-1
        >>> input_w0 = 0.8e-3
        >>> grating_width, grating_step, phase_depth = 8, 8, 1
        >>> grating_parameter = [grating_width, grating_step, phase_depth]
        >>> target_l = [-3, -1, 1, 3]
        >>> target_p = np.zeros_like(target_l)
        >>> target_weights = [0.4, 0.03, 0.07, 0.5]
        >>> img_path, img_name = "./img", "superposition_oam"
        >>> superposition_args = [slm_res, slm_pitch, input_w0, target_l, target_p, target_weights, True, False]
        >>> fields = generate_oam_superposition(*superposition_args)
        >>> hologram_args = [*fields, slm_pitch, *grating_parameter, True, False]
        >>> prepare_hologram = encode_hologram(*hologram_args)
        >>> hologram_args = hologram_args.append([True, img_path, img_name, False])
        >>> encode_hologram(*hologram_args)
    """

    if not use_inv_sinc_minus:
        modified_amp = 1 + (1/np.pi)*inv_sinc(Amp)
    elif use_inv_sinc_minus:
        modified_amp = 1 + (1/np.pi)*inv_sinc_minus(Amp)
    else:
        raise NotImplementedError("use_inv_sinc_minus argument must be True or False")
    modified_amp = modified_amp / np.max(modified_amp)
    modified_phase = Phase - np.pi*modified_amp

    parity = 0
    if prepare: parity = -1
    elif measure: parity = 1

    res = [np.shape(X)[1], np.shape(Y)[0]]
    hologram = modified_amp * np.mod(modified_phase + (parity * diffraction(d, N_steps, res)), 2*np.pi)


    hologram_final = cv2.normalize(hologram, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)

    if not save:
        return hologram_final
    elif save:
        if not os.path.exists(path):
            os.mkdir(path)
        cv2.imwrite(path+"/"+name+".bmp", hologram_final)
        return 0
    else:
        return 0

