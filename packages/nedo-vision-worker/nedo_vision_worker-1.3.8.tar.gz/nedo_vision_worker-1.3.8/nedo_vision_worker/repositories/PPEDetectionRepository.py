import os
import logging
from pathlib import Path
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from sqlalchemy.exc import SQLAlchemyError
from ..database.DatabaseManager import DatabaseManager, get_storage_path
from ..models.ppe_detection import PPEDetectionEntity
from ..models.ppe_detection_label import PPEDetectionLabelEntity

class PPEDetectionRepository:
    """Handles storage of PPE detections into SQLite using SQLAlchemy."""

    def __init__(self):
        
        self.storage_dir = get_storage_path("files")
        self.db_manager = DatabaseManager()
        self.session: Session = self.db_manager.get_session("default")
        os.makedirs(self.storage_dir, exist_ok=True) 

    
    def get_latest_detections(self, limit: int = 50) -> list:
        """
        Retrieves the latest PPE detections ordered by the 'created_at' timestamp.

        Args:
            limit (int): Maximum number of detections to retrieve. Default is 50.

        Returns:
            list: A list of PPE detection dictionaries.
        """
        try:
            latest_detections = (
                self.session.query(PPEDetectionEntity)
                .options(joinedload(PPEDetectionEntity.ppe_labels)) 
                .order_by(desc(PPEDetectionEntity.created_at))
                .limit(limit)
                .all()
            )
            
            # Prepare the list of UpsertPPEDetectionRequest messages
            ppe_detection_requests = []
            for detection in latest_detections:
                ppe_detection_labels = [
                    {
                        'code': label.code,
                        'confidence_score': label.confidence_score,
                        'b_box_x1': label.b_box_x1,
                        'b_box_y1': label.b_box_y2,
                        'b_box_x2': label.b_box_x2,
                        'b_box_y2': label.b_box_y2,
                    }
                    for label in detection.ppe_labels
                ]

                worker_timestamp = detection.created_at.strftime('%Y-%m-%dT%H:%M:%SZ')  # Remove microseconds and add Z for UTC

                # Create request object
                request = {
                    'person_id': detection.person_id,
                    'image': detection.image_path,
                    'image_tile': detection.image_tile_path,
                    'worker_source_id': detection.worker_source_id,
                    "worker_timestamp": worker_timestamp,
                    'ppe_detection_labels': ppe_detection_labels
                }
                ppe_detection_requests.append(request)
            
            return ppe_detection_requests

        except SQLAlchemyError as e:
            self.session.rollback()
            logging.error(f"❌ Database error while retrieving detections: {e}")
            return []

    def get_total_pending_count(self) -> int:
        """
        Returns the total count of pending PPE detections in the database.

        Returns:
            int: Total count of pending detections.
        """
        try:
            return self.session.query(PPEDetectionEntity).count()
        except SQLAlchemyError as e:
            logging.error(f"❌ Error counting pending detections: {e}")
            return 0

    def delete_records_from_db(self, detection_data: list):
        """
        Deletes PPE detection records from the database based on detection data.

        Args:
            detection_data (list): List of dictionaries containing the detection data.
        """
        if not detection_data:
            logging.info("No detection data provided for deletion.")
            return
            
        try:
            # Extract person_id from detection data to delete the corresponding records
            person_ids_to_delete = [data['person_id'] for data in detection_data]

            # Delete corresponding PPEDetectionEntity records
            detections_to_delete = (
                self.session.query(PPEDetectionEntity)
                .filter(PPEDetectionEntity.person_id.in_(person_ids_to_delete))
                .all()
            )

            for detection in detections_to_delete:
                # Also delete related PPE detection labels from PPEDetectionLabelEntity
                self.session.query(PPEDetectionLabelEntity).filter(PPEDetectionLabelEntity.detection_id == detection.id).delete()

                # Delete the image file associated with the detection if it exists
                image_path = detection.image_path
                if not os.path.isabs(image_path):
                    image_path = str(get_storage_path("files") / Path(image_path).relative_to("data/files"))
                if os.path.exists(image_path):
                    try:
                        os.remove(image_path)
                    except OSError as e:
                        logging.warning(f"Failed to delete image file {image_path}: {e}")
                else:
                    logging.warning(f"Image file not found for detection {detection.id}: {image_path}")
                
                # Delete the image tile file if it exists
                image_tile_path = detection.image_tile_path
                if image_tile_path:
                    if not os.path.isabs(image_tile_path):
                        image_tile_path = str(get_storage_path("files") / Path(image_tile_path).relative_to("data/files"))
                    if os.path.exists(image_tile_path):
                        try:
                            os.remove(image_tile_path)
                        except OSError as e:
                            logging.warning(f"Failed to delete image tile file {image_tile_path}: {e}")

                # Delete the detection record
                self.session.delete(detection)

            # Commit the transaction
            self.session.commit()
            logging.info(f"Successfully deleted {len(detections_to_delete)} PPE detection records.")

        except SQLAlchemyError as e:
            self.session.rollback()
            logging.error(f"❌ Error occurred while deleting records from DB: {e}")
