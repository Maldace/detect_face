from flask import Flask, request, render_template, Response  # import Flask và request
import base64                                        # decode base64
import numpy as np                                  # numpy cho mảng
import cv2                                          # OpenCV để xử lý ảnh
import threading                                     # thread để chạy imshow độc lập
import time                                          # sleep cho vòng lặp hiển thị
import detect

app = Flask(__name__, template_folder="templates")   # tạo app Flask

latest_frame = None                                  # biến toàn cục lưu frame mới nhất
frame_lock = threading.Lock()                        # khóa để tránh race condition

@app.route('/')
def index():                                         # route chính trả index.html
    return render_template('index.html')             # hiển thị giao diện

@app.route('/upload', methods=['POST'])
def upload():
    global latest_frame                               # tham chiếu biến toàn cục
    data = request.get_json()                         # lấy JSON từ request
    if not data or 'image' not in data:
        return 'No image', 400                        # trả lỗi nếu thiếu image

    # tách header 'data:image/jpeg;base64,...' lấy phần base64
    try:
        base64_str = data['image'].split(',', 1)[1]   # phần sau dấu phẩy là base64
    except Exception as e:
        print('Base64 split error:', e)
        return 'Bad image', 400

    # decode base64 thành bytes
    try:
        image_bytes = base64.b64decode(base64_str)
    except Exception as e:
        print('Base64 decode error:', e)
        return 'Decode error', 400

    # chuyển bytes sang numpy array rồi decode bằng OpenCV
    np_arr = np.frombuffer(image_bytes, np.uint8)     # tạo numpy từ bytes
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)      # decode ảnh

    if img is None:
        print('Decoded image is None, buffer size=', np_arr.size)  # debug
        return 'Bad decode', 400

    # lưu ảnh vào latest_frame (dùng lock để tránh tranh chấp)
    with frame_lock:
        latest_frame = img.copy()                     # copy để an toàn

    return '', 204                                     # trả No Content

def show_frames():                                    # hàm chạy trong thread riêng để hiển thị
    global latest_frame
    window_name = 'Webcam'                            # tên cửa sổ
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)   # tạo cửa sổ có thể resize
    cv2.resizeWindow(window_name, 800, 600)           # đặt kích thước cửa sổ mong muốn

    while True:
        frame = None
        with frame_lock:
            if latest_frame is not None:
                frame = latest_frame.copy()           # lấy bản sao frame hiện tại

        if frame is not None:
            # nếu cần resize hiển thị, có thể resize ở đây
            # frame = cv2.resize(frame, (640, 480))
            reg_frame=detect.draw_box(frame)
            cv2.imshow(window_name, reg_frame) 
            # # cv2.imshow(window_name, frame)            # hiển thị frame
            key = cv2.waitKey(1) & 0xFF               # cần waitKey để cửa sổ update
            if key == ord('q'):                       # nhấn 'q' để đóng (nếu muốn)
                break
              # encode ảnh thành jpeg
            # ret, buffer = cv2.imencode('.jpg', reg_frame)
            # frame_bytes = buffer.tobytes()

            # # yield ảnh liên tục
            # yield (b'--frame\r\n'
            #     b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
        else:
            # nếu chưa có frame nào, đợi 50ms rồi tiếp tục vòng lặp
            time.sleep(0.05)

    cv2.destroyAllWindows()                           # đóng cửa sổ khi thoát

# @app.route('/video_feed')
# def video_feed():
#     return Response(show_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    # tạo và start thread hiển thị trước khi chạy Flask
    t = threading.Thread(target=show_frames, daemon=True)  # thread daemon để tự dừng khi main kết thúc
    t.start()

    # chạy Flask, bật threaded=True để cho phép nhiều request đồng thời
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True, use_reloader=False)
