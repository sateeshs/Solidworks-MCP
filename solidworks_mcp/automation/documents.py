"""
SolidWorks Document Operations
------------------------------
Create, open, save, and manage SolidWorks documents.
"""

import os
import logging
import traceback
from typing import Optional, Dict

import win32com.client
import pythoncom

from ..constants import SwErrors, SwDocumentTypes, SwFileTypes, SwViews
from ..utils import find_template
from ..utils.com import com_get
from ..utils.tree_walk import walk_exhausted

logger = logging.getLogger(__name__)


class DocumentOperations:
    """
    Mixin class for document operations
    
    Requires parent class to have:
    - self._sw_app: SolidWorks application object
    - self.is_connected: Connection status property
    - self.connect(): Connection method
    - self._result(): Result factory method
    - self._units: UnitConverter instance
    """
    
    def create_new_part(self) -> Dict:
        """
        Create a new part document
        
        Returns:
            Result dictionary with document info
        """
        try:
            if not self.is_connected:
                r = self.connect()
                if not r["success"]:
                    return r
            
            # Find part template
            template = find_template("part")
            if not template:
                template = ""  # Let SolidWorks use default
                logger.info("Using SolidWorks default part template")
            else:
                logger.info(f"Using template: {template}")
            
            # Create document
            doc = self._sw_app.NewDocument(template, 0, 0, 0)
            
            if doc is None:
                return self._result(False, "Failed to create part document",
                                  SwErrors.swFileLoadError)
            
            # Set view
            try:
                doc.ShowNamedView2("*Isometric", 7)
                doc.ViewZoomtofit2()
            except:
                pass
            
            title = self._get_doc_title(doc)
            
            return self._result(True, f"Created part: {title}",
                              SwErrors.swSuccess,
                              {"name": title, "type": "Part"})
            
        except Exception as e:
            logger.error(f"Create part error: {e}\n{traceback.format_exc()}")
            return self._result(False, f"Error: {e}", SwErrors.swFileLoadError)
    
    def create_new_assembly(self) -> Dict:
        """
        Create a new assembly document
        
        Returns:
            Result dictionary with document info
        """
        try:
            if not self.is_connected:
                r = self.connect()
                if not r["success"]:
                    return r
            
            template = find_template("assembly")
            if not template:
                template = ""
            
            doc = self._sw_app.NewDocument(template, 0, 0, 0)
            
            if doc is None:
                return self._result(False, "Failed to create assembly",
                                  SwErrors.swFileLoadError)
            
            try:
                doc.ShowNamedView2("*Isometric", 7)
                doc.ViewZoomtofit2()
            except:
                pass
            
            title = self._get_doc_title(doc)
            
            return self._result(True, f"Created assembly: {title}",
                              SwErrors.swSuccess,
                              {"name": title, "type": "Assembly"})
            
        except Exception as e:
            logger.error(f"Create assembly error: {e}\n{traceback.format_exc()}")
            return self._result(False, f"Error: {e}", SwErrors.swFileLoadError)
    
    def create_new_drawing(self, paper_size: str = "A4") -> Dict:
        """
        Create a new drawing document
        
        Args:
            paper_size: Paper size (A4, A3, A2, A1, Letter)
        
        Returns:
            Result dictionary with document info
        """
        try:
            if not self.is_connected:
                r = self.connect()
                if not r["success"]:
                    return r
            
            template = find_template("drawing")
            if not template:
                template = ""
            
            doc = self._sw_app.NewDocument(template, 0, 0, 0)
            
            if doc is None:
                return self._result(False, "Failed to create drawing",
                                  SwErrors.swFileLoadError)
            
            title = self._get_doc_title(doc)
            
            return self._result(True, f"Created drawing: {title}",
                              SwErrors.swSuccess,
                              {"name": title, "type": "Drawing", "paper_size": paper_size})
            
        except Exception as e:
            logger.error(f"Create drawing error: {e}\n{traceback.format_exc()}")
            return self._result(False, f"Error: {e}", SwErrors.swFileLoadError)
    
    def open_document(self, filepath: str) -> Dict:
        """
        Open an existing document
        
        Args:
            filepath: Path to SolidWorks file
        
        Returns:
            Result dictionary
        """
        try:
            if not self.is_connected:
                r = self.connect()
                if not r["success"]:
                    return r
            
            if not os.path.exists(filepath):
                return self._result(False, f"File not found: {filepath}",
                                  SwErrors.swFileNotFoundError)
            
            # Determine document type from extension
            ext = os.path.splitext(filepath)[1].lower()
            type_map = {
                ".sldprt": SwDocumentTypes.swDocPART,
                ".sldasm": SwDocumentTypes.swDocASSEMBLY,
                ".slddrw": SwDocumentTypes.swDocDRAWING,
            }
            doc_type = type_map.get(ext, SwDocumentTypes.swDocPART)
            
            # Open document
            errors = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
            warnings = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
            
            doc = self._sw_app.OpenDoc6(filepath, int(doc_type), 0, "", errors, warnings)
            
            if doc is None or errors.value != 0:
                return self._result(False, f"Failed to open (error {errors.value})",
                                  SwErrors.swFileLoadError)
            
            title = self._get_doc_title(doc)
            
            return self._result(True, f"Opened: {title}",
                              SwErrors.swSuccess,
                              {"name": title, "path": filepath})
            
        except Exception as e:
            logger.error(f"Open document error: {e}\n{traceback.format_exc()}")
            return self._result(False, f"Error: {e}", SwErrors.swFileLoadError)
    
    def save_document(self, filepath: str = None) -> Dict:
        """
        Save the active document
        FIXED v4.1: Use doc.SaveAs() as primary method (avoids COM type mismatch
        with Extension.SaveAs where None parameter fails in SW 2025).
        
        Args:
            filepath: Path to save (None = save in place)
        
        Returns:
            Result dictionary
        """
        try:
            doc, err = self.get_active_doc()
            if err:
                return err
            
            if filepath:
                # Ensure absolute path
                filepath = os.path.abspath(filepath)
                
                # Ensure directory exists
                dir_path = os.path.dirname(filepath)
                if dir_path and not os.path.exists(dir_path):
                    os.makedirs(dir_path)
                
                saved = False
                method_used = ""
                
                # Method 1: doc.SaveAs (simplest, most reliable for SW 2025)
                try:
                    result = doc.SaveAs(filepath)
                    if result:
                        saved = True
                        method_used = "SaveAs"
                except Exception as e:
                    logger.debug(f"doc.SaveAs failed: {e}")
                
                # Method 2: Extension.SaveAs with proper VARIANT null dispatch
                if not saved:
                    try:
                        empty_export = win32com.client.VARIANT(pythoncom.VT_DISPATCH, None)
                        errors = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
                        warnings = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
                        
                        result = doc.Extension.SaveAs(
                            filepath, 0, 0, empty_export, errors, warnings
                        )
                        if result and errors.value == 0:
                            saved = True
                            method_used = "Extension.SaveAs"
                    except Exception as e:
                        logger.debug(f"Extension.SaveAs failed: {e}")
                
                # Method 3: Extension.SaveAs2
                if not saved:
                    try:
                        errors = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
                        warnings = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
                        
                        result = doc.Extension.SaveAs2(
                            filepath, 0, 0, None, "", False, errors, warnings
                        )
                        if result:
                            saved = True
                            method_used = "Extension.SaveAs2"
                    except Exception as e:
                        logger.debug(f"Extension.SaveAs2 failed: {e}")
                
                if not saved:
                    return self._result(False, "Save failed - all methods attempted",
                                      SwErrors.swFileSaveError)
                
                return self._result(True, f"Saved: {filepath} [{method_used}]",
                                  SwErrors.swSuccess,
                                  {"path": filepath, "method": method_used})
            else:
                # Save in place
                result = doc.Save3(0, 0, 0)
                
                if result != 0:
                    return self._result(False, f"Save failed (code {result})",
                                      SwErrors.swFileSaveError)
                
                path = self._get_doc_path(doc)
                return self._result(True, f"Saved: {path}",
                                  SwErrors.swSuccess, {"path": path})
            
        except Exception as e:
            logger.error(f"Save error: {e}\n{traceback.format_exc()}")
            return self._result(False, f"Error: {e}", SwErrors.swFileSaveError)
    
    def close_document(self, save: bool = False) -> Dict:
        """
        Close the active document
        
        Args:
            save: Save before closing
        
        Returns:
            Result dictionary
        """
        try:
            doc, err = self.get_active_doc()
            if err:
                return self._result(True, "No document to close")
            
            title = self._get_doc_title(doc)
            
            if save:
                doc.Save3(0, 0, 0)
            
            self._sw_app.CloseDoc(title)
            
            return self._result(True, f"Closed: {title}",
                              SwErrors.swSuccess, {"document": title})
            
        except Exception as e:
            logger.error(f"Close error: {e}\n{traceback.format_exc()}")
            return self._result(False, f"Error: {e}", SwErrors.swUnknownError)
    
    def get_document_info(self) -> Dict:
        """
        Get information about the active document
        
        Returns:
            Result dictionary with document details
        """
        try:
            doc, err = self.get_active_doc()
            if err:
                return err
            
            type_names = {
                0: "None",
                1: "Part",
                2: "Assembly",
                3: "Drawing"
            }
            
            doc_type = doc.GetType()
            title = self._get_doc_title(doc)
            path = self._get_doc_path(doc)
            
            info = {
                "title": title,
                "path": path if path else "Not saved",
                "type": type_names.get(doc_type, "Unknown"),
                "type_code": doc_type,
            }
            
            return self._result(True, f"{title} ({info['type']})",
                              SwErrors.swSuccess, info)
            
        except Exception as e:
            logger.error(f"Get info error: {e}\n{traceback.format_exc()}")
            return self._result(False, f"Error: {e}", SwErrors.swUnknownError)
    
    def list_open_documents(self) -> Dict:
        """
        List all open documents
        
        Returns:
            Result dictionary with document list
        """
        try:
            if not self.is_connected:
                r = self.connect()
                if not r["success"]:
                    return r
            
            docs = []
            doc = com_get(self._sw_app, "GetFirstDocument")

            walked = 0
            while doc:
                if walk_exhausted(walked, "open document list"):
                    break
                walked += 1
                try:
                    title = com_get(doc, "GetTitle")
                    doc_type = com_get(doc, "GetType")

                    type_names = {1: "Part", 2: "Assembly", 3: "Drawing"}

                    docs.append({
                        "title": title,
                        "type": type_names.get(doc_type, "Unknown")
                    })
                except:
                    pass

                doc = com_get(doc, "GetNext")
            
            return self._result(True, f"{len(docs)} document(s) open",
                              SwErrors.swSuccess, {"documents": docs})

        except Exception as e:
            logger.error(f"List documents error: {e}\n{traceback.format_exc()}")
            return self._result(False, f"Error: {e}", SwErrors.swUnknownError)

    # ========================================================================
    # Export
    # ========================================================================

    def export_step(self, filepath: str) -> Dict:
        """
        Export the active document to STEP format

        Args:
            filepath: Output file path (extension added if missing)

        Returns:
            Result dictionary
        """
        try:
            doc, err = self.get_active_doc()
            if err:
                return err

            if not filepath.lower().endswith(('.step', '.stp')):
                filepath += '.step'
            filepath = os.path.abspath(filepath)

            dir_path = os.path.dirname(filepath)
            if dir_path and not os.path.exists(dir_path):
                os.makedirs(dir_path)

            empty_export = win32com.client.VARIANT(pythoncom.VT_DISPATCH, None)
            errors = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
            warnings = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)

            result = doc.Extension.SaveAs(
                filepath, 0, 0, empty_export, errors, warnings
            )

            if not result or errors.value != 0:
                return self._result(False,
                    f"STEP export failed (error code {errors.value})",
                    SwErrors.swExportError)

            return self._result(True, f"Exported to STEP: {filepath}",
                              SwErrors.swSuccess, {"path": filepath})

        except Exception as e:
            logger.error(f"Export STEP error: {e}\n{traceback.format_exc()}")
            return self._result(False, f"Error: {e}", SwErrors.swExportError)

    def export_stl(self, filepath: str, binary: bool = True) -> Dict:
        """
        Export the active document to STL format (for 3D printing)

        Args:
            filepath: Output file path (extension added if missing)
            binary: True for binary STL, False for ASCII (best-effort - the
                   document's current STL export preference may override this)

        Returns:
            Result dictionary
        """
        try:
            doc, err = self.get_active_doc()
            if err:
                return err

            if not filepath.lower().endswith('.stl'):
                filepath += '.stl'
            filepath = os.path.abspath(filepath)

            dir_path = os.path.dirname(filepath)
            if dir_path and not os.path.exists(dir_path):
                os.makedirs(dir_path)

            saved = False
            method_used = ""

            # Method 1: Extension.SaveAs (format inferred from extension)
            try:
                empty_export = win32com.client.VARIANT(pythoncom.VT_DISPATCH, None)
                errors = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
                warnings = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)

                result = doc.Extension.SaveAs(
                    filepath, 0, 0, empty_export, errors, warnings
                )
                if result and errors.value == 0:
                    saved = True
                    method_used = "Extension.SaveAs"
            except Exception as e:
                logger.debug(f"STL Extension.SaveAs failed: {e}")

            # Method 2: SaveAs4 (older SW, explicit binary flag)
            if not saved:
                try:
                    result = doc.SaveAs4(filepath, 0, 1 if binary else 0, False)
                    if result:
                        saved = True
                        method_used = "SaveAs4"
                except Exception as e:
                    logger.debug(f"STL SaveAs4 failed: {e}")

            if not saved:
                return self._result(False, "STL export failed - all methods attempted",
                                  SwErrors.swExportError)

            return self._result(True, f"STL exported: {filepath} [{method_used}]",
                              SwErrors.swSuccess,
                              {"path": filepath, "binary": binary,
                               "api_method": method_used})

        except Exception as e:
            logger.error(f"Export STL error: {e}\n{traceback.format_exc()}")
            return self._result(False, f"Error: {e}", SwErrors.swExportError)

    def export_dxf(self, filepath: str) -> Dict:
        """
        Export the active document (drawing sheet or part flat pattern) to DXF

        Args:
            filepath: Output file path (extension added if missing)

        Returns:
            Result dictionary
        """
        try:
            doc, err = self.get_active_doc()
            if err:
                return err

            if not filepath.lower().endswith('.dxf'):
                filepath += '.dxf'
            filepath = os.path.abspath(filepath)

            dir_path = os.path.dirname(filepath)
            if dir_path and not os.path.exists(dir_path):
                os.makedirs(dir_path)

            empty_export = win32com.client.VARIANT(pythoncom.VT_DISPATCH, None)
            errors = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
            warnings = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)

            result = doc.Extension.SaveAs(
                filepath, 0, 0, empty_export, errors, warnings
            )

            if not result or errors.value != 0:
                return self._result(False,
                    f"DXF export failed (error code {errors.value})",
                    SwErrors.swExportError)

            return self._result(True, f"Exported to DXF: {filepath}",
                              SwErrors.swSuccess, {"path": filepath})

        except Exception as e:
            logger.error(f"Export DXF error: {e}\n{traceback.format_exc()}")
            return self._result(False, f"Error: {e}", SwErrors.swExportError)

    # ========================================================================
    # Undo / Redo
    # ========================================================================

    def undo(self) -> Dict:
        """
        Undo the last operation in the active document

        Returns:
            Result dictionary

        Note: EditUndo2 lives on IModelDoc2 (doc), not the Application object,
        and its dynamic-dispatch return value is unreliable (observed None on
        a confirmed-successful undo - verified live 2026-09-22 by checking
        feature count before/after). Success here means the call didn't raise.
        """
        try:
            doc, err = self.get_active_doc()
            if err:
                return err

            doc.EditUndo2(1)
            return self._result(True, "Undo successful", SwErrors.swSuccess)

        except Exception as e:
            logger.error(f"Undo error: {e}\n{traceback.format_exc()}")
            return self._result(False, f"Error: {e}", SwErrors.swUnknownError)

    def redo(self) -> Dict:
        """
        Redo the last undone operation in the active document

        Returns:
            Result dictionary

        Note: see undo() - EditRedo2 lives on doc, return value is unreliable.
        """
        try:
            doc, err = self.get_active_doc()
            if err:
                return err

            doc.EditRedo2(1)
            return self._result(True, "Redo successful", SwErrors.swSuccess)

        except Exception as e:
            logger.error(f"Redo error: {e}\n{traceback.format_exc()}")
            return self._result(False, f"Error: {e}", SwErrors.swUnknownError)

    # ========================================================================
    # View Control
    # ========================================================================

    def capture_view(self, filepath: str, width: int = 1920, height: int = 1080) -> Dict:
        """
        Capture the current model view as an image

        Args:
            filepath: Output image path (.bmp; other extensions are saved as
                     BMP data since SaveBMP is the only capture API available)
            width: Image width in pixels
            height: Image height in pixels

        Returns:
            Result dictionary
        """
        try:
            doc, err = self.get_active_doc()
            if err:
                return err

            filepath = os.path.abspath(filepath)
            dir_path = os.path.dirname(filepath)
            if dir_path and not os.path.exists(dir_path):
                os.makedirs(dir_path)

            result = doc.SaveBMP(filepath, width, height)

            if not result:
                return self._result(False, "Failed to capture view",
                                  SwErrors.swFileSaveError)

            return self._result(True, f"Captured: {filepath}",
                              SwErrors.swSuccess,
                              {"path": filepath, "width": width, "height": height})

        except Exception as e:
            logger.error(f"Capture view error: {e}\n{traceback.format_exc()}")
            return self._result(False, f"Error: {e}", SwErrors.swFileSaveError)

    def zoom_fit(self) -> Dict:
        """
        Zoom the active view to fit all geometry

        Returns:
            Result dictionary
        """
        try:
            doc, err = self.get_active_doc()
            if err:
                return err

            doc.ViewZoomtofit2()
            return self._result(True, "Zoomed to fit", SwErrors.swSuccess)

        except Exception as e:
            logger.error(f"Zoom fit error: {e}\n{traceback.format_exc()}")
            return self._result(False, f"Error: {e}", SwErrors.swUnknownError)

    def set_view(self, view_name: str = "isometric") -> Dict:
        """
        Set the active document to a standard named view

        Args:
            view_name: "front", "back", "left", "right", "top", "bottom",
                      "isometric", "trimetric", or "dimetric"

        Returns:
            Result dictionary
        """
        try:
            doc, err = self.get_active_doc()
            if err:
                return err

            view_data = SwViews.get(view_name)

            doc.ShowNamedView2(view_data[0], view_data[1])
            doc.ViewZoomtofit2()

            return self._result(True, f"Set view: {view_name}",
                              SwErrors.swSuccess, {"view": view_name})

        except Exception as e:
            logger.error(f"Set view error: {e}\n{traceback.format_exc()}")
            return self._result(False, f"Error: {e}", SwErrors.swUnknownError)
