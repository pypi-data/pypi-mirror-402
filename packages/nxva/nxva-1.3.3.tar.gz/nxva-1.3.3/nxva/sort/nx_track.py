import numpy as np
import time

from .kalmanfilter import KalmanFilter
from .utils.tools import mean_to_xyxy

def convert_x_to_bbox(x, score=None):
    """
    Takes a bounding box in the centre form [x,y,s,r] and returns it in the form
      [x1,y1,x2,y2] where x1,y1 is the top left and x2,y2 is the bottom right
    """
    w = np.sqrt(x[2] * x[3])
    h = x[2] / w
    if(score == None):
      return np.array([x[0]-w/2., x[1]-h/2., x[0]+w/2., x[1]+h/2.]).reshape((1, 4))
    else:
      return np.array([x[0]-w/2., x[1]-h/2., x[0]+w/2., x[1]+h/2., score]).reshape((1, 5))

def check_if_bbox_valid(bbox):
    """
    Check if the bounding box is valid.
    A bounding box is considered valid if its width and height are greater than zero.
    Also, we have to make sure that the x1, y1, x2, y2 are positive and not infinite or nan.
    """
    if bbox.shape[0] < 4:
        return False
    x1, y1, x2, y2 = bbox[:4]
    if x1 >= x2 or y1 >= y2:
        return False
    if np.any(np.isinf(bbox)) or np.any(np.isnan(bbox)):
        return False
    if x1 < 0 or y1 < 0 or x2 < 0 or y2 < 0:
        return False
    return True

def _cosine_distance(a, b, data_is_normalized=False):
    """Compute pair-wise cosine distance between points in `a` and `b`.
    Parameters
    ----------
    a : array_like
        An NxM matrix of N samples of dimensionality M.
    b : array_like
        An LxM matrix of L samples of dimensionality M.
    data_is_normalized : Optional[bool]
        If True, assumes rows in a and b are unit length vectors.
        Otherwise, a and b are explicitly normalized to lenght 1.
    Returns
    -------
    ndarray
        Returns a matrix of size len(a), len(b) such that eleement (i, j)
        contains the squared distance between `a[i]` and `b[j]`.
    """
    if not data_is_normalized:
        a = np.asarray(a) / np.linalg.norm(a, axis=1, keepdims=True)
        b = np.asarray(b) / np.linalg.norm(b, axis=1, keepdims=True)
        
    return 1. - np.dot(a, b.T)

def cosine_distance_to_image_center(bbox, image_size):
    """
    Calculates the absolute cosine distance subtracted by 1, from an up vector located at the image center to
    the specified bbox.

    Inputs:
        bbox - bounding box of type (x pos, y pos, s area, r aspect ratio), shape (1, 4)
        image_size - tuple (width, height)

    Returns:
        Absolute value of cosine distance subtracted by 1 (higher values means further away from up vector located
        at image center)
    """
    up_vector = np.asarray([[0., 1., 0., 0.]])
    image_center_pos = np.asarray([[image_size[0] / 2., image_size[1] / 2., 0., 0.]])
    
    return np.abs(_cosine_distance(up_vector, bbox - image_center_pos).flatten() - 1)[0]

def convert_bbox_to_xyah(bbox):
    """
    Takes a bounding box in the form [x1,y1,x2,y2] and returns z in the form
      [cx,cy,a,h] where cx,cy is the centre of the box and a is the aspect ratio and h is the height
    """
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    cx = bbox[0] + w/2.
    cy = bbox[1] + h/2.
    a = w / float(h+1e-6)
    
    return np.array([cx, cy, a, h])

def convert_bbox_to_z(bbox):
    """
    Takes a bounding box in the form [x1,y1,x2,y2] and returns z in the form
      [x,y,s,r] where x,y is the centre of the box and s is the scale/area and r is
      the aspect ratio
    """
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    x = bbox[0] + w/2.
    y = bbox[1] + h/2.
    s = w * h  # scale is just area
    r = w / float(h+1e-6)
    
    return np.array([x, y, s, r]).reshape((4, 1))

class TrackState:
    """
    Enum for tracking states.
    """
    INITIAL = 1
    CONFIRMED = 2
    DELETED = 3
    
class NXTracker(object):
    def __init__(self, bbox, max_age, min_hits, delta_t=3,
                 use_kalman_filter=False, image_size=(0, 0), dir_history_num=10, uid=None):
        """
        Args:
            bbox: initial bounding box
            max_age: maximum number of frames to tolerate disappear
            min_hits: minimum number of hits to confirm a track
            use_kalman_filter: whether to use Kalman filter for tracking
            image_size: size of the image for bounding box normalization
            dir_history_num: number of history frames for direction calculation
        """
        self.bbox = bbox
        self.max_age = max_age
        self.min_hits = min_hits
        self.use_kalman_filter = use_kalman_filter
        self.image_size = image_size
        self.dir_history_num = dir_history_num
        self.state = TrackState.INITIAL

        self.time_since_update = 0
        self.last_predict_bbox = bbox
        self.history_bbox = [bbox]
        self.hits = 0
        self.uid = uid if uid is not None else -1

        self.features = [] # List to store features for this track

        """
        NOTE: [-1,-1,-1,-1,-1] is a compromising placeholder for non-observation status, the same for the return of 
        function k_previous_obs. It is ugly and I do not like it. But to support generate observation array in a 
        fast and unified way, which you would see below k_observations = np.array([k_previous_obs(...]]), let's bear it for now.
        """
        self.velocity = None
        self.delta_t = delta_t

        self.last_update_time = time.time()

        if self.use_kalman_filter:
            self.kf = KalmanFilter()
            self.mean, self.covariance = self.kf.initiate(convert_bbox_to_xyah(bbox))

    def predict(self):
        """
        若有用 Kalman filter，則返回上一幀的預測框；
        否則返回上一幀的實際框。
        """
        self.time_since_update += 1
        if self.use_kalman_filter:
            self.mean, self.covariance = self.kf.predict(self.mean, self.covariance)
            last_bbox = mean_to_xyxy(self.mean)
            # If the predicted bounding box is not valid, use the last observed bounding box
            if not check_if_bbox_valid(last_bbox):
                last_bbox = self.history_bbox[-1][:4]
        else:
            last_bbox = self.history_bbox[-1][:4]
            # If not using Kalman filter, just return the last bounding box
        self.last_predict_bbox = last_bbox
        return last_bbox

    def update(self, bbox):
        if bbox is not None:
            self.time_since_update = 0
            self.hits += 1
            if self.state == TrackState.INITIAL and self.hits >= self.min_hits:
                self.state = TrackState.CONFIRMED
            if self.use_kalman_filter:
                self.mean, self.covariance = self.kf.update(self.mean, self.covariance, convert_bbox_to_xyah(bbox), bbox[4])

            self.bbox = bbox[:4]  # Update the bounding box
            self.history_bbox.append(bbox[:4])
            if len(self.history_bbox) > self.dir_history_num:
                self.history_bbox = self.history_bbox[-self.dir_history_num:]
            self.last_update_time = time.time()
        else:
            pass

    
    def mark_missed(self):
        """Mark this track as missed (no association at the current time step).
        """
        if self.state == TrackState.INITIAL:
            self.state = TrackState.DELETED
        elif self.time_since_update > self.max_age:
            self.state = TrackState.DELETED
    
    def push_feature(self, feature):
        """Add a feature to the track's feature list.
        
        Args:
            feature: The feature to be added.
        """
        if feature.ndim > 1:
            feature = feature.flatten()
        self.features.append(feature)
        self.features = self.features[-self.max_age:]  # Keep only the most recent features


    def is_initial(self):
        """Returns True if this track is tentative (unconfirmed).
        """
        return self.state == TrackState.INITIAL

    def is_confirmed(self):
        """Returns True if this track is confirmed."""
        return self.state == TrackState.CONFIRMED

    def is_deleted(self):
        """Returns True if this track is dead and should be deleted."""
        return self.state == TrackState.DELETED    
