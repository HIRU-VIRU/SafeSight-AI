"""
Dashboard API for SafeSight AI.
Flask REST API for violation analytics, data export, and inference control.
"""

from flask import Flask, jsonify, request, send_file, send_from_directory, Response
from flask_cors import CORS
from datetime import date, datetime
from pathlib import Path
import tempfile
import threading
import time
import cv2

from services.database import DatabaseService
from config.settings import API_HOST, API_PORT, API_DEBUG, CAMERA_ID, STORAGE_PATH, BASE_DIR


# Global registry of running inference threads so the API can report / control them
_active_streams: dict = {}  # stream_id -> {"thread": Thread, "pipeline": InferencePipeline, "source": str}
_streams_lock = threading.Lock()


def create_app():
    """Create and configure Flask application."""
    app = Flask(__name__)
    CORS(app)  # Enable CORS for frontend access
    
    # Initialize database service
    db = DatabaseService()
    
    @app.route('/')
    def index():
        """API root endpoint."""
        return jsonify({
            "service": "SafeSight AI Dashboard API",
            "version": "1.0.0",
            "endpoints": {
                "violations_today": "/violations/today",
                "violations_count": "/violations/count",
                "violations_recent": "/violations/recent",
                "violations_hourly": "/violations/hourly",
                "violations_export": "/violations/export"
            }
        })
    
    @app.route('/violations/today', methods=['GET'])
    def get_today_violations():
        """
        Get all violations from today.
        
        Query params:
            camera_id: Optional camera filter
            
        Returns:
            JSON array of violation records
        """
        try:
            camera_id = request.args.get('camera_id')
            violations = db.get_today_violations(camera_id=camera_id)
            
            return jsonify({
                "success": True,
                "count": len(violations),
                "date": date.today().isoformat(),
                "violations": violations
            })
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
    
    @app.route('/violations/recent', methods=['GET'])
    def get_recent_violations():
        """
        Get recent violations.
        
        Query params:
            limit: Number of records to return (default 10, max 100)
            
        Returns:
            JSON array of recent violation records
        """
        try:
            limit = min(int(request.args.get('limit', 10)), 100)
            violations = db.get_recent_violations(limit=limit)
            
            return jsonify({
                "success": True,
                "count": len(violations),
                "violations": violations
            })
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
    
    @app.route('/violations/count', methods=['GET'])
    def get_violation_count():
        """
        Get total violation count.
        
        Query params:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            camera_id: Optional camera filter
            
        Returns:
            JSON with total count
        """
        try:
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            camera_id = request.args.get('camera_id')
            
            count = db.get_violation_count(
                start_date=start_date,
                end_date=end_date,
                camera_id=camera_id
            )
            
            return jsonify({
                "success": True,
                "count": count,
                "filters": {
                    "start_date": start_date,
                    "end_date": end_date,
                    "camera_id": camera_id
                }
            })
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
    
    @app.route('/violations/hourly', methods=['GET'])
    def get_hourly_stats():
        """
        Get hourly violation statistics.
        
        Query params:
            date: Target date (YYYY-MM-DD, default today)
            
        Returns:
            JSON array of hourly statistics
        """
        try:
            target_date = request.args.get('date')
            if target_date is None:
                target_date = date.today().isoformat()
            
            stats = db.get_hourly_stats(target_date=target_date)
            
            return jsonify({
                "success": True,
                "date": target_date,
                "hourly_stats": stats
            })
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
    
    @app.route('/violations/export', methods=['GET'])
    def export_violations():
        """
        Export violations to CSV file.
        
        Query params:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            CSV file download
        """
        try:
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(
                mode='w', 
                delete=False, 
                suffix='.csv'
            )
            temp_file.close()
            
            # Export to CSV
            success = db.export_csv(
                output_path=temp_file.name,
                start_date=start_date,
                end_date=end_date
            )
            
            if success:
                return send_file(
                    temp_file.name,
                    mimetype='text/csv',
                    as_attachment=True,
                    download_name=f'violations_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
                )
            else:
                return jsonify({
                    "success": False,
                    "error": "No data to export"
                }), 404
                
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
    
    @app.route('/violations/stats', methods=['GET'])
    def get_statistics():
        """
        Get overall statistics.
        
        Returns:
            JSON with statistics summary
        """
        try:
            today = date.today().isoformat()
            
            today_count = db.get_violation_count(start_date=today, end_date=today)
            total_count = db.get_violation_count()
            recent = db.get_recent_violations(limit=5)
            
            return jsonify({
                "success": True,
                "stats": {
                    "today_violations": today_count,
                    "total_violations": total_count,
                    "recent_violations": len(recent)
                },
                "recent": recent
            })
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
    
    @app.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint."""
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat()
        })

    # ------------------------------------------------------------------ new endpoints

    @app.route('/violations/filter', methods=['GET'])
    def get_filtered_violations():
        """
        Get violations with camera / date / severity filters + pagination.

        Query params:
            camera_id, date (YYYY-MM-DD), severity (critical|warning),
            limit (default 200), offset (default 0)
        """
        try:
            camera_id = request.args.get('camera_id')
            date_str = request.args.get('date')
            severity = request.args.get('severity')
            limit = min(int(request.args.get('limit', 200)), 1000)
            offset = int(request.args.get('offset', 0))

            violations = db.get_filtered_violations(
                camera_id=camera_id,
                date_str=date_str,
                severity=severity,
                limit=limit,
                offset=offset,
            )
            return jsonify({"success": True, "count": len(violations), "violations": violations})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route('/violations/cameras', methods=['GET'])
    def get_cameras():
        """Return distinct camera IDs."""
        try:
            cameras = db.get_distinct_cameras()
            return jsonify({"success": True, "cameras": cameras})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route('/violations/dates', methods=['GET'])
    def get_dates():
        """Return distinct violation dates."""
        try:
            dates = db.get_distinct_dates()
            return jsonify({"success": True, "dates": dates})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route('/violations/severity-counts', methods=['GET'])
    def get_severity_counts():
        """
        Get violation counts grouped by severity.

        Query params: camera_id, date
        """
        try:
            camera_id = request.args.get('camera_id')
            date_str = request.args.get('date')
            counts = db.get_severity_counts(camera_id=camera_id, date_str=date_str)
            return jsonify({"success": True, **counts})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route('/violations/image/<path:image_path>', methods=['GET'])
    def serve_violation_image(image_path: str):
        """
        Serve a violation evidence image.

        The image_path stored in the DB is relative to <project>/storage/
        e.g. "violations/2026-02-25/camera_01_..._person3.jpg"
        """
        try:
            storage_root = Path(BASE_DIR) / 'storage'
            full = (storage_root / image_path).resolve()
            # Security: ensure it stays within storage
            if not str(full).startswith(str(storage_root.resolve())):
                return jsonify({"success": False, "error": "Invalid path"}), 403
            if not full.exists():
                return jsonify({"success": False, "error": "Image not found"}), 404
            return send_file(str(full), mimetype='image/jpeg')
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    # ------------------------------------------------------------------ inference control

    @app.route('/inference/start', methods=['POST'])
    def start_inference():
        """
        Start inference on a video source.

        JSON body: { "source": "<url or path>", "stream_id": "optional_label" }
        """
        try:
            data = request.get_json(force=True)
            source = data.get('source', '').strip()
            if not source:
                return jsonify({"success": False, "error": "source is required"}), 400

            stream_id = data.get('stream_id', '').strip()
            if not stream_id:
                stream_id = f"api_stream_{len(_active_streams) + 1}"

            with _streams_lock:
                if stream_id in _active_streams:
                    return jsonify({"success": False, "error": f"Stream '{stream_id}' already running"}), 409

            # Lazy imports to avoid circular deps at module load time
            from core.inference import InferencePipeline

            pipeline = InferencePipeline(stream_id=stream_id)

            def _run():
                try:
                    pipeline.run_video(source, display=False)
                finally:
                    with _streams_lock:
                        _active_streams.pop(stream_id, None)

            t = threading.Thread(target=_run, name=f"api-{stream_id}", daemon=True)
            with _streams_lock:
                _active_streams[stream_id] = {
                    "thread": t,
                    "pipeline": pipeline,
                    "source": source,
                    "started_at": datetime.now().isoformat(),
                }
            t.start()

            return jsonify({"success": True, "stream_id": stream_id, "source": source})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route('/inference/status', methods=['GET'])
    def inference_status():
        """List running inference streams."""
        with _streams_lock:
            streams = []
            for sid, info in _active_streams.items():
                streams.append({
                    "stream_id": sid,
                    "source": info["source"],
                    "started_at": info["started_at"],
                    "alive": info["thread"].is_alive(),
                })
        return jsonify({"success": True, "streams": streams})

    @app.route('/inference/stop', methods=['POST'])
    def stop_inference():
        """
        Stop a running inference stream.

        JSON body: { "stream_id": "..." }
        NOTE: Graceful stop is limited — we remove the entry but the
        thread will finish when the video ends or on next exception.
        """
        try:
            data = request.get_json(force=True)
            stream_id = data.get('stream_id', '').strip()
            with _streams_lock:
                info = _active_streams.pop(stream_id, None)
            if info is None:
                return jsonify({"success": False, "error": "Stream not found"}), 404
            return jsonify({"success": True, "stopped": stream_id})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route('/inference/stream/<stream_id>', methods=['GET'])
    def stream_video(stream_id: str):
        """
        MJPEG stream of annotated inference frames for a running stream.
        Use as <img src=".../inference/stream/my_stream"> in the browser.
        """
        def generate():
            while True:
                with _streams_lock:
                    info = _active_streams.get(stream_id)
                if info is None:
                    break
                pipeline = info.get("pipeline")
                if pipeline is None:
                    break
                frame = pipeline.get_latest_frame()
                if frame is not None:
                    _, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
                time.sleep(0.05)  # ~20 fps cap

        return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')
    
    return app


def run_api_server(host: str = API_HOST, port: int = API_PORT, debug: bool = API_DEBUG):
    """
    Run the Flask API server.
    
    Args:
        host: Host address
        port: Port number
        debug: Debug mode
    """
    app = create_app()
    
    print("\n" + "="*50)
    print("SafeSight AI Dashboard API")
    print("="*50)
    print(f"🌐 Server: http://{host}:{port}")
    print(f"📊 Endpoints available at http://{host}:{port}/")
    print("="*50 + "\n")
    
    app.run(host=host, port=port, debug=debug, threaded=True)


if __name__ == "__main__":
    run_api_server()
