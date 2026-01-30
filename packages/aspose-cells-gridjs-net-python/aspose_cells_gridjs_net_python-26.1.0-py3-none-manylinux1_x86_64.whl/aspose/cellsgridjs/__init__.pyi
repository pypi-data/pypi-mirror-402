
from typing import List, Optional, Dict, Iterable, Any, overload
import io
import collections.abc
from collections.abc import Sequence
from datetime import datetime
from aspose.pyreflection import Type
import aspose.pycore
import aspose.pydrawing
from uuid import UUID
import aspose.cellsgridjs

class CoWorkUserProvider:
    '''Represents the user provider inerface in collabration mode.only available in java version now, will be available in .net/python version in future.
    Customer application can implement this interface to provide the user information.'''
    
    def get_current_user_name(self) -> str:
        '''Gets the username of the current user
        
        :returns: Current username'''
        raise NotImplementedError()
    
    def get_current_user_id(self) -> int:
        '''Gets the unique identifier of the current user
        
        :returns: Current user ID'''
        raise NotImplementedError()
    
    def get_permission(self) -> aspose.cellsgridjs.CoWorkUserPermission:
        '''Gets the permission level of the current user
        
        :returns: Current user permission level'''
        raise NotImplementedError()
    

class Config:
    '''Represents all the static settings for GridJs'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @overload
    @staticmethod
    def set_license(license_name : str) -> None:
        '''Licenses the component.
        
        :param license_name: Can be a full or short file name or name of an embedded resource.
        Use an empty string to switch to evaluation mode.'''
        raise NotImplementedError()
    
    @overload
    @staticmethod
    def set_license(stream : io._IOBase) -> None:
        '''Licenses the component.
        
        :param stream: A stream that contains the license.'''
        raise NotImplementedError()
    
    @staticmethod
    def set_font_folder(font_folder : str, recursive : bool) -> None:
        '''Sets the fonts folder
        
        :param font_folder: The folder that contains TrueType fonts.
        :param recursive: Determines whether or not to scan subfolders.'''
        raise NotImplementedError()
    
    @staticmethod
    def set_font_folders(font_folders : List[str], recursive : bool) -> None:
        '''Sets the fonts folders
        
        :param font_folders: The folders that contains TrueType fonts.
        :param recursive: Determines whether or not to scan subfolders.'''
        raise NotImplementedError()
    
    @staticmethod
    def set_save_html_as_zip(value: bool) -> None:
        '''Gets/Sets  whether to save html file as zip archive,the default is false.'''
    @property
    def save_html_as_zip(self) -> bool:
        '''Gets/Sets  whether to save html file as zip archive,the default is false.'''
        raise NotImplementedError()

    @staticmethod
    def set_skip_invisible_shapes(value: bool) -> None:
        '''Gets/Sets  whether to skip shapes that are invisble to UI ,the default value is true.'''
    @property
    def skip_invisible_shapes(self) -> bool:
        '''Gets/Sets  whether to skip shapes that are invisble to UI ,the default value is true.'''
        raise NotImplementedError()

    @staticmethod
    def set_lazy_loading(value: bool) -> None:
        '''Gets/Sets  whether to load active worksheet only,the default is false.'''
    @property
    def lazy_loading(self) -> bool:
        '''Gets/Sets  whether to load active worksheet only,the default is false.'''
        raise NotImplementedError()

    @staticmethod
    def set_same_image_detecting(value: bool) -> None:
        '''Gets/Sets  whether to check if images have same source,the default is true
        the default value is true.'''
    @property
    def same_image_detecting(self) -> bool:
        '''Gets/Sets  whether to check if images have same source,the default is true
        the default value is true.'''
        raise NotImplementedError()

    @staticmethod
    def set_auto_optimize_for_large_cells(value: bool) -> None:
        '''Gets/Sets  whether to automatically optimize the load performance for worksheet with large cells.
        it will ignore some style /borders to reduce the load  time.
        the default value is true.'''
    @property
    def auto_optimize_for_large_cells(self) -> bool:
        '''Gets/Sets  whether to automatically optimize the load performance for worksheet with large cells.
        it will ignore some style /borders to reduce the load  time.
        the default value is true.'''
        raise NotImplementedError()

    @staticmethod
    def set_islimit_shape_or_image(value: bool) -> None:
        '''Gets/Sets  whether to limit the total display shape/image count in one worksheet ,if set to true,
        GridJs will limit the total count of the display shapes or images in one worksheet  to MaxShapeOrImageCount
        the default value is true.'''
    @property
    def islimit_shape_or_image(self) -> bool:
        '''Gets/Sets  whether to limit the total display shape/image count in one worksheet ,if set to true,
        GridJs will limit the total count of the display shapes or images in one worksheet  to MaxShapeOrImageCount
        the default value is true.'''
        raise NotImplementedError()

    @staticmethod
    def set_max_shape_or_image_count(value: int) -> None:
        '''Gets/Sets the total count of the display shapes or images in the active sheet,it takes effect  when IslimitShapeOrImage=true.
        the default value is 100.'''
    @property
    def max_shape_or_image_count(self) -> int:
        '''Gets/Sets the total count of the display shapes or images in the active sheet,it takes effect  when IslimitShapeOrImage=true.
        the default value is 100.'''
        raise NotImplementedError()

    @staticmethod
    def set_max_total_shape_or_image_count(value: int) -> None:
        '''Gets/Sets the total count of the display shapes or images  in the workbook,it takes effect  when IslimitShapeOrImage=true.
        the default value is 300.'''
    @property
    def max_total_shape_or_image_count(self) -> int:
        '''Gets/Sets the total count of the display shapes or images  in the workbook,it takes effect  when IslimitShapeOrImage=true.
        the default value is 300.'''
        raise NotImplementedError()

    @staticmethod
    def set_max_shape_or_image_width_or_height(value: int) -> None:
        '''Gets/Sets the  max width or height for a shape or an image ,GridJs will ignore the shape or image with the width or height larger than this, it takes effect when IslimitShapeOrImage=true.
        the default value is 10000.'''
    @property
    def max_shape_or_image_width_or_height(self) -> int:
        '''Gets/Sets the  max width or height for a shape or an image ,GridJs will ignore the shape or image with the width or height larger than this, it takes effect when IslimitShapeOrImage=true.
        the default value is 10000.'''
        raise NotImplementedError()

    @staticmethod
    def set_max_pdf_save_seconds(value: int) -> None:
        '''Gets/Sets the max timed out seconds when save to PDF.
        the default value is 10.'''
    @property
    def max_pdf_save_seconds(self) -> int:
        '''Gets/Sets the max timed out seconds when save to PDF.
        the default value is 10.'''
        raise NotImplementedError()

    @staticmethod
    def set_ignore_empty_content(value: bool) -> None:
        '''Gets/Sets whether to show  the max range which includes data ,style, merged cells and shapes.
        if the last row or column contains cells with  no value and formula but has custom style
        then we will not show this row/column when this vlaue is true。
        the default value is true .'''
    @property
    def ignore_empty_content(self) -> bool:
        '''Gets/Sets whether to show  the max range which includes data ,style, merged cells and shapes.
        if the last row or column contains cells with  no value and formula but has custom style
        then we will not show this row/column when this vlaue is true。
        the default value is true .'''
        raise NotImplementedError()

    @staticmethod
    def set_use_print_area(value: bool) -> None:
        '''Gets/Sets whether to use PageSetup.PrintArea for the UI display range when the worksheet has PageSetup setting for PrintArea.
        the default value is false .'''
    @property
    def use_print_area(self) -> bool:
        '''Gets/Sets whether to use PageSetup.PrintArea for the UI display range when the worksheet has PageSetup setting for PrintArea.
        the default value is false .'''
        raise NotImplementedError()

    @staticmethod
    def set_is_collaborative(value: bool) -> None:
        '''Gets/Sets  whether to support collabrative editing,the default is false.'''
    @property
    def is_collaborative(self) -> bool:
        '''Gets/Sets  whether to support collabrative editing,the default is false.'''
        raise NotImplementedError()

    @staticmethod
    def set_custom_pdf_save_options(value: aspose.cellsgridjs.PdfSaveOptions) -> None:
        '''Gets/Sets the custom PdfSaveOptions for PDF export. If set, this will be used instead of the default options.
        the default value is null.'''
    @property
    def custom_pdf_save_options(self) -> aspose.cellsgridjs.PdfSaveOptions:
        '''Gets/Sets the custom PdfSaveOptions for PDF export. If set, this will be used instead of the default options.
        the default value is null.'''
        raise NotImplementedError()

    @staticmethod
    def set_load_time_out(value: int) -> None:
        '''Gets/Sets a timeout interrupt in milliseconds in loading file, when the cost time period of loading file  is longer than the expectation   ，it will raise exception.
        the default value is -1,which means no timeout interrupt is set .'''
    @property
    def load_time_out(self) -> int:
        '''Gets/Sets a timeout interrupt in milliseconds in loading file, when the cost time period of loading file  is longer than the expectation   ，it will raise exception.
        the default value is -1,which means no timeout interrupt is set .'''
        raise NotImplementedError()

    @staticmethod
    def set_show_chart_sheet(value: bool) -> None:
        '''Gets/Sets whether to show chart worksheet.
        the default value is false .'''
    @property
    def show_chart_sheet(self) -> bool:
        '''Gets/Sets whether to show chart worksheet.
        the default value is false .'''
        raise NotImplementedError()

    @staticmethod
    def set_empty_sheet_max_row(value: int) -> None:
        '''Gets/Sets default max row for an empty worksheet.
        the default value is 12.'''
    @property
    def empty_sheet_max_row(self) -> int:
        '''Gets/Sets default max row for an empty worksheet.
        the default value is 12.'''
        raise NotImplementedError()

    @staticmethod
    def set_empty_sheet_max_col(value: int) -> None:
        '''Gets/Sets default max column for an empty worksheet.
        the default value is 15.'''
    @property
    def empty_sheet_max_col(self) -> int:
        '''Gets/Sets default max column for an empty worksheet.
        the default value is 15.'''
        raise NotImplementedError()

    @staticmethod
    def set_picture_cache_directory(value: str) -> None:
        '''Gets/Sets the cache directory for pictures.(this takes effect when GridJsWorkbook.CacheImp is null)
        the default path will be "_piccache" inside the FileCacheDirectory.'''
    @property
    def picture_cache_directory(self) -> str:
        '''Gets/Sets the cache directory for pictures.(this takes effect when GridJsWorkbook.CacheImp is null)
        the default path will be "_piccache" inside the FileCacheDirectory.'''
        raise NotImplementedError()

    @staticmethod
    def set_file_cache_directory(value: str) -> None:
        '''Gets/Sets the cache directory for storing spreadsheet file.
        We need to set it to a specific path before we use GridJs.'''
    @property
    def file_cache_directory(self) -> str:
        '''Gets/Sets the cache directory for storing spreadsheet file.
        We need to set it to a specific path before we use GridJs.'''
        raise NotImplementedError()

    @staticmethod
    def set_base_route_name(value: str) -> None:
        '''Gets/Sets the base route name for GridJs controller URL. the default is "/GridJs2".'''
    @property
    def base_route_name(self) -> str:
        '''Gets/Sets the base route name for GridJs controller URL. the default is "/GridJs2".'''
        raise NotImplementedError()

    @staticmethod
    def set_message_topic(value: str) -> None:
        '''Gets/Sets the websocket destinations prefixed with "/topic". the default is "/topic/opr".used in collaborative mode only.'''
    @property
    def message_topic(self) -> str:
        '''Gets/Sets the websocket destinations prefixed with "/topic". the default is "/topic/opr".used in collaborative mode only.'''
        raise NotImplementedError()

    @staticmethod
    def set_auto_fit_rows_height_on_load(value: bool) -> None:
        '''Indicates whether to autofit rows height  when loading the file,the default value is false.'''
    @property
    def auto_fit_rows_height_on_load(self) -> bool:
        '''Indicates whether to autofit rows height  when loading the file,the default value is false.'''
        raise NotImplementedError()


class GridAbstractCalculationEngine:
    '''Represents user\'s custom calculation engine to extend the default calculation engine of Aspose.Cells.'''
    
    def calculate(self, data : aspose.cellsgridjs.GridCalculationData) -> None:
        '''Calculates one function with given data.
        
        :param data: The required data to calculate function such as function name, parameters, ...etc.'''
        raise NotImplementedError()
    

class GridCacheForStream:
    '''This class contains the cache operations for GridJs. User shall implement his own business logic for storage based on it..'''
    
    def save_stream(self, s : io._IOBase, uid : str) -> None:
        '''Implements this method to save cache,save the stream to the cache with the key uid.'''
        raise NotImplementedError()
    
    def load_stream(self, uid : str) -> io._IOBase:
        '''Implements this method to load cache with the key uid,return the stream from the cache.'''
        raise NotImplementedError()
    
    def is_existed(self, uid : str) -> bool:
        '''Checks whether the cache with uid is existed
        
        :param uid: The unique id for the file cache.
        :returns: The bool value'''
        raise NotImplementedError()
    
    def get_file_url(self, uid : str) -> str:
        '''Implements this method to get the file url  from the cache.
        
        :param uid: The unique id for the file cache.
        :returns: The URL of the file'''
        raise NotImplementedError()
    

class GridCalculationData:
    '''Represents the required data when calculating one function, such as function name, parameters, ...etc.'''
    
    def get_param_value(self, index : int) -> Any:
        '''Gets the represented value object of the parameter at given index.
        
        :param index: The index of the parameter(0 based).
        :returns: If the parameter is plain value, then returns the plain value.
        If the parameter is reference, then return ReferredArea object.'''
        raise NotImplementedError()
    
    def get_param_text(self, index : int) -> str:
        '''Gets the literal text of the parameter at given index.
        
        :param index: The index of the parameter(0 based).
        :returns: The literal text of the parameter.'''
        raise NotImplementedError()
    
    @property
    def calculated_value(self) -> Any:
        '''Gets/sets the calculated value for this function.'''
        raise NotImplementedError()
    
    @calculated_value.setter
    def calculated_value(self, value : Any) -> None:
        '''Gets/sets the calculated value for this function.'''
        raise NotImplementedError()
    
    @property
    def row(self) -> int:
        '''Gets the Cell Row index where the function is in.'''
        raise NotImplementedError()
    
    @property
    def column(self) -> int:
        '''Gets the Cell Column index where the function is in.'''
        raise NotImplementedError()
    
    @property
    def string_value(self) -> str:
        '''Gets the Cell DisplayStringValue where the function is in.'''
        raise NotImplementedError()
    
    @property
    def value(self) -> Any:
        '''Gets the Cell value where the function is in.'''
        raise NotImplementedError()
    
    @property
    def formula(self) -> str:
        '''Gets the Cell formula where the function is in.'''
        raise NotImplementedError()
    
    @property
    def sheet_name(self) -> str:
        '''Gets the worksheet name where the function is in.'''
        raise NotImplementedError()
    
    @property
    def function_name(self) -> str:
        '''Gets the function name to be calculated.'''
        raise NotImplementedError()
    
    @property
    def param_count(self) -> int:
        '''Gets the count of parameters .'''
        raise NotImplementedError()
    

class GridCellException:
    '''The exception that is thrown when GridJs specified error occurs.'''
    
    def to_string(self) -> str:
        '''Creates and returns a string representation of the current exception.'''
        raise NotImplementedError()
    
    @property
    def code(self) -> aspose.cellsgridjs.GridExceptionType:
        '''Represents the exception code.'''
        raise NotImplementedError()
    

class GridJsControllerBase:
    
    def __init__(self, grid_js_service : aspose.cellsgridjs.IGridJsService) -> None:
        raise NotImplementedError()
    

class GridJsOptions:
    '''Represents  all the load options for GridJs'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @property
    def save_html_as_zip(self) -> bool:
        '''Gets/Sets  whether to save html file as zip archive,the default is false.'''
        raise NotImplementedError()
    
    @save_html_as_zip.setter
    def save_html_as_zip(self, value : bool) -> None:
        '''Gets/Sets  whether to save html file as zip archive,the default is false.'''
        raise NotImplementedError()
    
    @property
    def skip_invisible_shapes(self) -> bool:
        '''Gets/Sets  whether to skip shapes that are invisble to UI ,the default value is true.'''
        raise NotImplementedError()
    
    @skip_invisible_shapes.setter
    def skip_invisible_shapes(self, value : bool) -> None:
        '''Gets/Sets  whether to skip shapes that are invisble to UI ,the default value is true.'''
        raise NotImplementedError()
    
    @property
    def lazy_loading(self) -> bool:
        '''Gets/Sets  whether to load active worksheet only,the default is false.'''
        raise NotImplementedError()
    
    @lazy_loading.setter
    def lazy_loading(self, value : bool) -> None:
        '''Gets/Sets  whether to load active worksheet only,the default is false.'''
        raise NotImplementedError()
    
    @property
    def same_image_detecting(self) -> bool:
        '''Gets/Sets  whether to check if images have same source,the default is true
        the default value is true.'''
        raise NotImplementedError()
    
    @same_image_detecting.setter
    def same_image_detecting(self, value : bool) -> None:
        '''Gets/Sets  whether to check if images have same source,the default is true
        the default value is true.'''
        raise NotImplementedError()
    
    @property
    def auto_optimize_for_large_cells(self) -> bool:
        '''Gets/Sets  whether to automatically optimize the load performance for worksheet with large cells.
        it will ignore some style /borders to reduce the load  time.
        the default value is true.'''
        raise NotImplementedError()
    
    @auto_optimize_for_large_cells.setter
    def auto_optimize_for_large_cells(self, value : bool) -> None:
        '''Gets/Sets  whether to automatically optimize the load performance for worksheet with large cells.
        it will ignore some style /borders to reduce the load  time.
        the default value is true.'''
        raise NotImplementedError()
    
    @property
    def islimit_shape_or_image(self) -> bool:
        '''Gets/Sets  whether to limit the total display shape/image count in one worksheet ,if set to true,
        GridJs will limit the total count of the display shapes or images in one worksheet  to MaxShapeOrImageCount
        the default value is true.'''
        raise NotImplementedError()
    
    @islimit_shape_or_image.setter
    def islimit_shape_or_image(self, value : bool) -> None:
        '''Gets/Sets  whether to limit the total display shape/image count in one worksheet ,if set to true,
        GridJs will limit the total count of the display shapes or images in one worksheet  to MaxShapeOrImageCount
        the default value is true.'''
        raise NotImplementedError()
    
    @property
    def max_shape_or_image_count(self) -> int:
        '''Gets/Sets the total count of the display shapes or images in the active sheet,it takes effect  when IslimitShapeOrImage=true.
        the default value is 100.'''
        raise NotImplementedError()
    
    @max_shape_or_image_count.setter
    def max_shape_or_image_count(self, value : int) -> None:
        '''Gets/Sets the total count of the display shapes or images in the active sheet,it takes effect  when IslimitShapeOrImage=true.
        the default value is 100.'''
        raise NotImplementedError()
    
    @property
    def max_total_shape_or_image_count(self) -> int:
        '''Gets/Sets the total count of the display shapes or images  in the workbook,it takes effect  when IslimitShapeOrImage=true.
        the default value is 300.'''
        raise NotImplementedError()
    
    @max_total_shape_or_image_count.setter
    def max_total_shape_or_image_count(self, value : int) -> None:
        '''Gets/Sets the total count of the display shapes or images  in the workbook,it takes effect  when IslimitShapeOrImage=true.
        the default value is 300.'''
        raise NotImplementedError()
    
    @property
    def max_shape_or_image_width_or_height(self) -> int:
        '''Gets/Sets the  max width or height for a shape or an image ,GridJs will ignore the shape or image with the width or height larger than this, it takes effect when IslimitShapeOrImage=true.
        the default value is 10000.'''
        raise NotImplementedError()
    
    @max_shape_or_image_width_or_height.setter
    def max_shape_or_image_width_or_height(self, value : int) -> None:
        '''Gets/Sets the  max width or height for a shape or an image ,GridJs will ignore the shape or image with the width or height larger than this, it takes effect when IslimitShapeOrImage=true.
        the default value is 10000.'''
        raise NotImplementedError()
    
    @property
    def max_pdf_save_seconds(self) -> int:
        '''Gets/Sets the max timed out seconds when save to PDF.
        the default value is 10.'''
        raise NotImplementedError()
    
    @max_pdf_save_seconds.setter
    def max_pdf_save_seconds(self, value : int) -> None:
        '''Gets/Sets the max timed out seconds when save to PDF.
        the default value is 10.'''
        raise NotImplementedError()
    
    @property
    def ignore_empty_content(self) -> bool:
        '''Gets/Sets whether to show  the max range which includes data ,style, merged cells and shapes.
        if the last row or column contains cells with  no value and formula but has custom style
        then we will not show this row/column when this vlaue is true。
        the default value is true .'''
        raise NotImplementedError()
    
    @ignore_empty_content.setter
    def ignore_empty_content(self, value : bool) -> None:
        '''Gets/Sets whether to show  the max range which includes data ,style, merged cells and shapes.
        if the last row or column contains cells with  no value and formula but has custom style
        then we will not show this row/column when this vlaue is true。
        the default value is true .'''
        raise NotImplementedError()
    
    @property
    def use_print_area(self) -> bool:
        '''Gets/Sets whether to use PageSetup.PrintArea for the UI display range when the worksheet has PageSetup setting for PrintArea.
        the default value is false .'''
        raise NotImplementedError()
    
    @use_print_area.setter
    def use_print_area(self, value : bool) -> None:
        '''Gets/Sets whether to use PageSetup.PrintArea for the UI display range when the worksheet has PageSetup setting for PrintArea.
        the default value is false .'''
        raise NotImplementedError()
    
    @property
    def is_collaborative(self) -> bool:
        '''Gets/Sets  whether to support collabrative editing,the default is false.'''
        raise NotImplementedError()
    
    @is_collaborative.setter
    def is_collaborative(self, value : bool) -> None:
        '''Gets/Sets  whether to support collabrative editing,the default is false.'''
        raise NotImplementedError()
    
    @property
    def custom_pdf_save_options(self) -> aspose.cellsgridjs.PdfSaveOptions:
        '''Gets/Sets the custom PdfSaveOptions for PDF export. If set, this will be used instead of the default options.
        the default value is null.'''
        raise NotImplementedError()
    
    @custom_pdf_save_options.setter
    def custom_pdf_save_options(self, value : aspose.cellsgridjs.PdfSaveOptions) -> None:
        '''Gets/Sets the custom PdfSaveOptions for PDF export. If set, this will be used instead of the default options.
        the default value is null.'''
        raise NotImplementedError()
    
    @property
    def load_time_out(self) -> int:
        '''Gets/Sets a timeout interrupt in milliseconds in loading file, when the cost time period of loading file  is longer than the expectation   ，it will raise exception.
        the default value is -1,which means no timeout interrupt is set .'''
        raise NotImplementedError()
    
    @load_time_out.setter
    def load_time_out(self, value : int) -> None:
        '''Gets/Sets a timeout interrupt in milliseconds in loading file, when the cost time period of loading file  is longer than the expectation   ，it will raise exception.
        the default value is -1,which means no timeout interrupt is set .'''
        raise NotImplementedError()
    
    @property
    def show_chart_sheet(self) -> bool:
        '''Gets/Sets whether to show chart worksheet.
        the default value is false .'''
        raise NotImplementedError()
    
    @show_chart_sheet.setter
    def show_chart_sheet(self, value : bool) -> None:
        '''Gets/Sets whether to show chart worksheet.
        the default value is false .'''
        raise NotImplementedError()
    
    @property
    def empty_sheet_max_row(self) -> int:
        '''Gets/Sets default max row for an empty worksheet.
        the default value is 12.'''
        raise NotImplementedError()
    
    @empty_sheet_max_row.setter
    def empty_sheet_max_row(self, value : int) -> None:
        '''Gets/Sets default max row for an empty worksheet.
        the default value is 12.'''
        raise NotImplementedError()
    
    @property
    def empty_sheet_max_col(self) -> int:
        '''Gets/Sets default max column for an empty worksheet.
        the default value is 15.'''
        raise NotImplementedError()
    
    @empty_sheet_max_col.setter
    def empty_sheet_max_col(self, value : int) -> None:
        '''Gets/Sets default max column for an empty worksheet.
        the default value is 15.'''
        raise NotImplementedError()
    
    @property
    def picture_cache_directory(self) -> str:
        '''Gets/Sets the cache directory for pictures.(this takes effect when GridJsWorkbook.CacheImp is null)
        the default path will be "_piccache" inside the FileCacheDirectory.'''
        raise NotImplementedError()
    
    @picture_cache_directory.setter
    def picture_cache_directory(self, value : str) -> None:
        '''Gets/Sets the cache directory for pictures.(this takes effect when GridJsWorkbook.CacheImp is null)
        the default path will be "_piccache" inside the FileCacheDirectory.'''
        raise NotImplementedError()
    
    @property
    def file_cache_directory(self) -> str:
        '''Gets/Sets the cache directory for storing spreadsheet file.
        We need to set it to a specific path before we use GridJs.'''
        raise NotImplementedError()
    
    @file_cache_directory.setter
    def file_cache_directory(self, value : str) -> None:
        '''Gets/Sets the cache directory for storing spreadsheet file.
        We need to set it to a specific path before we use GridJs.'''
        raise NotImplementedError()
    
    @property
    def font_folders(self) -> List[str]:
        '''Gets/Sets the fonts folders for fonts in the rendered pictures/shapes'''
        raise NotImplementedError()
    
    @font_folders.setter
    def font_folders(self, value : List[str]) -> None:
        '''Gets/Sets the fonts folders for fonts in the rendered pictures/shapes'''
        raise NotImplementedError()
    
    @property
    def base_route_name(self) -> str:
        '''Gets/Sets the route URL base name for GridJs controller.the default is GridJs2'''
        raise NotImplementedError()
    
    @base_route_name.setter
    def base_route_name(self, value : str) -> None:
        '''Gets/Sets the route URL base name for GridJs controller.the default is GridJs2'''
        raise NotImplementedError()
    
    @property
    def message_topic(self) -> str:
        '''Gets/Sets the websocket destinations prefixed with "/topic". the default is "/topic/opr".used in collaborative mode only.'''
        raise NotImplementedError()
    
    @message_topic.setter
    def message_topic(self, value : str) -> None:
        '''Gets/Sets the websocket destinations prefixed with "/topic". the default is "/topic/opr".used in collaborative mode only.'''
        raise NotImplementedError()
    
    @property
    def auto_fit_rows_height_on_load(self) -> bool:
        '''Indicates whether to autofit rows height  when loading the file,the default value is false.'''
        raise NotImplementedError()
    
    @auto_fit_rows_height_on_load.setter
    def auto_fit_rows_height_on_load(self, value : bool) -> None:
        '''Indicates whether to autofit rows height  when loading the file,the default value is false.'''
        raise NotImplementedError()
    
    @property
    def cache_imp(self) -> aspose.cellsgridjs.GridCacheForStream:
        '''Custom  implemention for cache storage,If you want to store cache in stream way ,you  need to set and implement it.'''
        raise NotImplementedError()
    
    @cache_imp.setter
    def cache_imp(self, value : aspose.cellsgridjs.GridCacheForStream) -> None:
        '''Custom  implemention for cache storage,If you want to store cache in stream way ,you  need to set and implement it.'''
        raise NotImplementedError()
    

class GridJsPermissionException:
    '''represents permission exception in collaboration mode.only available in java version now, will be available in .net/python version in future.'''
    
    @overload
    def __init__(self, operation : str, required_permission : aspose.cellsgridjs.CoWorkUserPermission, current_permission : aspose.cellsgridjs.CoWorkUserPermission) -> None:
        '''Constructs a permission exception
        
        :param operation: Operation attempted to execute
        :param required_permission: Permission required for the operation
        :param current_permission: Current user permission'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, message : str, operation : str, required_permission : aspose.cellsgridjs.CoWorkUserPermission, current_permission : aspose.cellsgridjs.CoWorkUserPermission) -> None:
        '''Constructs a permission exception
        
        :param message: Custom error message
        :param operation: Operation attempted to execute
        :param required_permission: Permission required for the operation
        :param current_permission: Current user permission'''
        raise NotImplementedError()
    
    def get_required_permission(self) -> aspose.cellsgridjs.CoWorkUserPermission:
        '''Gets the permission level required for the operation
        
        :returns: Required permission level'''
        raise NotImplementedError()
    
    def get_current_permission(self) -> aspose.cellsgridjs.CoWorkUserPermission:
        '''Gets the current permission level of the user
        
        :returns: Current user permission level'''
        raise NotImplementedError()
    
    def get_operation(self) -> str:
        '''Gets the operation that was attempted to execute
        
        :returns: Operation name'''
        raise NotImplementedError()
    

class GridJsService(IGridJsService):
    '''Provides the basic operation apis used in controller actions.'''
    
    def __init__(self, options : aspose.cellsgridjs.GridJsOptions) -> None:
        '''The default constructor for GridJsService'''
        raise NotImplementedError()
    
    def check_in_cache_for_collaborative(self, uid : str) -> bool:
        '''Check wether workbook instance is in memory cache .this method is apply for Collaborative mode only.'''
        raise NotImplementedError()
    
    def update_cell(self, p : str, uid : str) -> str:
        '''Applies the update operation.
        
        :param p: The JSON format string of update operation.
        :param uid: The unique id for the file cache.
        :returns: The JSON format string of the update result.'''
        raise NotImplementedError()
    
    def detail_stream_json_with_uid(self, stream : io._IOBase, file_path : str, uid : str) -> None:
        '''Write the JSON string  for the file to the stream  by the specified unique id.
        
        :param stream: The stream that will be written
        :param file_path: The file path
        :param uid: The unique id for the file cache.'''
        raise NotImplementedError()
    
    def detail_stream_json(self, stream : io._IOBase, file_path : str) -> None:
        '''Write the JSON string  for the file to the stream .
        
        :param stream: The stream that will be written
        :param file_path: The file path'''
        raise NotImplementedError()
    
    def lazy_loading_stream_json(self, stream : io._IOBase, sheet_name : str, uid : str) -> None:
        '''Writes the JSON string of the specified sheet in the file from the cache using the specified unique id  to the stream..
        
        :param stream: The stream that will be written
        :param sheet_name: The sheet name.
        :param uid: The unique id for the file cache.'''
        raise NotImplementedError()
    
    def add_image(self, p : str, uid : str, iscontrol : str, file_input_stream : io._IOBase) -> str:
        '''Applies the add image from local file operation.
        
        :param p: The JSON string parameter
        :param uid: The unique id for the file cache.
        :param iscontrol: Specify whether it is a control.
        :param file_input_stream: The input stream form file of the image
        :returns: The JSON string result'''
        raise NotImplementedError()
    
    def add_image_by_url(self, p : str, uid : str, imageurl : str) -> str:
        '''Applies the add image from remote URL operation.
        
        :param p: The JSON string parameter
        :param uid: The unique id for the file cache.
        :param imageurl: Specify the image URL.
        :returns: The JSON string result'''
        raise NotImplementedError()
    
    def copy_image(self, p : str, uid : str) -> str:
        '''Applies the copy image operation.
        
        :param p: The JSON string parameter
        :param uid: The unique id for the file cache.
        :returns: The JSON string result'''
        raise NotImplementedError()
    
    def load(self, uid : str, filename : str) -> str:
        '''Gets the JSON  string  of the file from the cache using the specified unique id,set the output filename in the JSON.
        
        :param uid: The unique id for the file cache.
        :param filename: Specifies the file name in the JSON. If set to null,the default filename is: book1.
        :returns: The JSON string'''
        raise NotImplementedError()
    
    def image(self, uid : str, picid : str) -> io._IOBase:
        '''Get Stream of image.
        
        :param uid: The unique id for the file cache.
        :param picid: The image id.
        :returns: The image stream'''
        raise NotImplementedError()
    
    def ole(self, uid : str, sheetname : str, oleid : int, label : List[str]) -> List[int]:
        '''Gets the byte array data of the  embedded ole object .
        
        :param uid: The unique id for the file cache.
        :param sheetname: The worksheet name.
        :param oleid: The  id for the embedded ole object.
        :param label: The display label of the embedded ole object.
        :returns: The byte array data of the  embedded ole object .'''
        raise NotImplementedError()
    
    def image_url(self, base_url : str, picid : str, uid : str) -> str:
        '''Gets the image URL.
        
        :param base_url: The base action URL.
        :param picid: The image id.
        :param uid: The unique id for the file cache.
        :returns: The image URL'''
        raise NotImplementedError()
    
    def get_file(self, fileid : str) -> io._IOBase:
        '''Get file stream
        
        :param fileid: the file id
        :returns: The stream of the file'''
        raise NotImplementedError()
    
    def download(self, p : str, uid : str, filename : str) -> str:
        '''Applies the download file operation
        
        :param p: The JSON parameter
        :param uid: The unique id for the file cache.
        :param filename: The file name
        :returns: The file URL'''
        raise NotImplementedError()
    
    @property
    def settings(self) -> aspose.cellsgridjs.GridWorkbookSettings:
        '''Represents the workbook settings.'''
        raise NotImplementedError()
    
    @settings.setter
    def settings(self, value : aspose.cellsgridjs.GridWorkbookSettings) -> None:
        '''Represents the workbook settings.'''
        raise NotImplementedError()
    

class GridJsWorkbook:
    '''Represents the main entry class for GridJs'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @overload
    def import_excel_file(self, uid : str, file_name : str, password : str) -> None:
        '''Imports the excel file from file path and open password.
        
        :param uid: The unique id for the file cache, if set to null,it will be generated automatically.
        :param file_name: The full path of the file.
        :param password: The open password  of the excel file.The value can be null If no passowrd is set.'''
        raise NotImplementedError()
    
    @overload
    def import_excel_file(self, uid : str, file_name : str) -> None:
        '''Imports the excel file from the file path.
        
        :param uid: The unique id for the file cache, if set to null,it will be generated automatically.
        :param file_name: The full path of the file.'''
        raise NotImplementedError()
    
    @overload
    def import_excel_file(self, file_name : str) -> None:
        '''Imports the excel file from the file path.
        
        :param file_name: The full path of the file.'''
        raise NotImplementedError()
    
    @overload
    def import_excel_file(self, uid : str, filestream : io._IOBase, format : aspose.cellsgridjs.GridLoadFormat, password : str) -> None:
        '''Imports the excel file from  file stream with load format and open password.
        
        :param uid: The unique id for the file cache, if set to null,it will be generated automatically.
        :param filestream: The stream of the excel file .
        :param format: The LoadFormat of the excel file.
        :param password: The open password  of the excel file.The value can be null If no passowrd is set'''
        raise NotImplementedError()
    
    @overload
    def import_excel_file(self, uid : str, filestream : io._IOBase, format : aspose.cellsgridjs.GridLoadFormat) -> None:
        '''Imports the excel file from file stream.
        
        :param uid: The unique id for the file cache, if set to null,it will be generated automatically.
        :param filestream: The stream of the excel file .
        :param format: The LoadFormat of the excel file.'''
        raise NotImplementedError()
    
    @overload
    def import_excel_file(self, filestream : io._IOBase, format : aspose.cellsgridjs.GridLoadFormat, password : str) -> None:
        '''Imports the excel file from file stream with load format and open password.
        
        :param filestream: The stream of the excel file .
        :param format: The LoadFormat of the excel file.
        :param password: The open password  of the excel file.The value can be null If no passowrd is set.'''
        raise NotImplementedError()
    
    @overload
    def import_excel_file(self, filestream : io._IOBase, format : aspose.cellsgridjs.GridLoadFormat) -> None:
        '''Imports the excel file from file stream with load format.
        
        :param filestream: The stream of the excel file .
        :param format: The LoadFormat of the excel file.'''
        raise NotImplementedError()
    
    @overload
    def export_to_json(self, filename : str) -> str:
        '''Gets JSON  string from memory data,set the output filename in the JSON.
        
        :param filename: Specifies the file name in the JSON. If set to null,the default filename is: book1..
        :returns: The JSON string.'''
        raise NotImplementedError()
    
    @overload
    def export_to_json(self) -> str:
        '''Gets JSON string from memory data, the default filename in the JSON is: book1.
        
        :returns: The JSON string.'''
        raise NotImplementedError()
    
    @overload
    def save_to_excel_file(self, stream : io._IOBase) -> None:
        '''Saves the memory data to the sream, baseed on the origin file format.
        
        :param stream: The stream to save.'''
        raise NotImplementedError()
    
    @overload
    def save_to_excel_file(self, path : str) -> None:
        '''Saves the memory data to the file path,if the file has extension ,save format is baseed on the file extension .
        
        :param path: The file path to save.'''
        raise NotImplementedError()
    
    @overload
    def save_to_pdf(self, path : str) -> None:
        '''Saves the memory data to the file path,the save format is pdf.
        
        :param path: The file path to save.'''
        raise NotImplementedError()
    
    @overload
    def save_to_pdf(self, stream : io._IOBase) -> None:
        '''Saves the memory data to the sream,the save format is pdf.
        
        :param stream: The stream to save.'''
        raise NotImplementedError()
    
    @overload
    def save_to_xlsx(self, path : str) -> None:
        '''Saves the memory data to the file path,the save format is xlsx.
        
        :param path: The file path to save.'''
        raise NotImplementedError()
    
    @overload
    def save_to_xlsx(self, stream : io._IOBase) -> None:
        '''Saves the memory data to the sream,the save format is xlsx.
        
        :param stream: The stream to save.'''
        raise NotImplementedError()
    
    @overload
    def save_to_html(self, path : str) -> None:
        '''Saves the memory data to the file path,the save format is html.
        
        :param path: The file path to save.'''
        raise NotImplementedError()
    
    @overload
    def save_to_html(self, stream : io._IOBase) -> None:
        '''Saves the memory data to the sream,the save format is html
        
        :param stream: The stream to save.'''
        raise NotImplementedError()
    
    def json_to_stream_by_uid(self, stream : io._IOBase, uid : str, filename : str) -> bool:
        '''Retrieve the JSON string of the file from the cache using the specified unique id,set the output filename in the JSON,and write it to the stream.
        
        :param stream: The stream that will be written
        :param uid: The unique id for the file cache.
        :param filename: Specifies the file name in the JSON. If set to null,the default filename is: book1.'''
        raise NotImplementedError()
    
    def json_to_stream(self, stream : io._IOBase, filename : str) -> None:
        '''Retrieve the JSON string from memory data,set the output filename in the JSON, and write it to the stream.
        
        :param stream: The stream that will be written
        :param filename: Specifies the file name in the JSON. If set to null,the default filename is: book1.'''
        raise NotImplementedError()
    
    def lazy_loading_stream(self, stream : io._IOBase, uid : str, sheet_name : str) -> None:
        '''Retrieve the JSON string of the specified sheet in the file from the cache using the specified unique id, and write it to the stream.
        
        :param stream: The stream that will be written
        :param uid: The unique id for the file cache.
        :param sheet_name: the sheet name.'''
        raise NotImplementedError()
    
    def get_json_str_by_uid(self, uid : str, filename : str) -> str:
        '''Gets the JSON  string  of the file from the cache using the specified unique id,set the output filename in the JSON.
        
        :param uid: The unique id for the file cache.
        :param filename: Specifies the file name in the JSON. If set to null,the default filename is: book1.
        :returns: The JSON  string'''
        raise NotImplementedError()
    
    def lazy_loading_json_str(self, uid : str, sheet_name : str) -> str:
        '''Gets the JSON string of the specified sheet in the file from the cache using the specified unique id.
        
        :param uid: The unique id for the file cache.
        :param sheet_name: the sheet name .
        :returns: The JSON string'''
        raise NotImplementedError()
    
    @staticmethod
    def get_uid_for_file(file_name : str) -> str:
        '''Generates a new unique id for the file cache using the given file name.
        
        :param file_name: The file name.'''
        raise NotImplementedError()
    
    def import_excel_file_from_json(self, json : str) -> None:
        '''Imports the excel file from JSON format string.
        
        :param json: The JSON format string.'''
        raise NotImplementedError()
    
    def merge_excel_file_from_json(self, uid : str, json : str) -> None:
        '''Applies a batch update to the memory data.
        
        :param uid: The unique id for the file cache.
        :param json: The update JSON format string.'''
        raise NotImplementedError()
    
    def save_to_cache_with_file_name(self, uid : str, filename : str, password : str) -> None:
        '''Saves the memory data to the cache file with the specified filename and also set the open password, the save format is baseed on the file extension of the filename  .
        
        :param uid: The unique id for the file cache.
        :param filename: The filename to save.
        :param password: The excel file\'s open password. The value can be null If no passowrd is set.'''
        raise NotImplementedError()
    
    @staticmethod
    def get_image_stream(uid : str, picid : str) -> io._IOBase:
        '''Get Stream of image.
        
        :param uid: The unique id for the file cache.
        :param picid: The image id.
        :returns: The image stream'''
        raise NotImplementedError()
    
    def get_ole(self, uid : str, sheetname : str, oleid : int, label : List[str]) -> List[int]:
        '''Gets the byte array data of the  embedded ole object .
        
        :param uid: The unique id for the file cache.
        :param sheetname: The worksheet name.
        :param oleid: The  id for the embedded ole object.
        :param label: The display label of the embedded ole object.
        :returns: The byte array data of the  embedded ole object .'''
        raise NotImplementedError()
    
    def check_in_cache_for_collaborative(self, uid : str) -> bool:
        '''Check wether workbook instance is in memory cache .this method is apply for Collaborative mode only.'''
        raise NotImplementedError()
    
    def update_cell(self, p : str, uid : str) -> str:
        '''Applies the update operation.
        
        :param p: The JSON format string of update operation.
        :param uid: The unique id for the file cache.
        :returns: The JSON format string of the update result.'''
        raise NotImplementedError()
    
    def insert_image(self, uid : str, p : str, s : io._IOBase, image_url : str) -> str:
        '''Inserts image in the worksheet from file stream or the URL,(either the file stream or the URL shall be provided)
        or
        Inserts shape ,when the p.type is one of AutoShapeType
        
        :param uid: The unique id for the file cache
        :param p: The JSON format string for the operation which specify the cell location  ,the worksheet name,upper left row,upper left column for the image，etc  {name:\'sheet1\',ri:1,ci:1}
        :param s: The file stream of the image file
        :param image_url: The URL of the image file
        :returns: The JSON format string of the inserted image'''
        raise NotImplementedError()
    
    def copy_image_or_shape(self, uid : str, p : str) -> str:
        '''Copys image or shape.
        
        :param uid: The unique id for the file cache.
        :param p: The JSON string for the operation which specify the cell location ,it contains the worksheet name,upper left row,upper left column for the image or shape，etc  {name:\'sheet1\',ri:1,ci:1,srcid:2,srcname:\'sheet2\',isshape:true}
        :returns: The JSON string of the new copied image'''
        raise NotImplementedError()
    
    def error_json(self, msg : str) -> str:
        '''Gets the error message string in JSON format.
        
        :param msg: The error message.
        :returns: The JSON string.'''
        raise NotImplementedError()
    
    @staticmethod
    def get_grid_load_format(extension : str) -> aspose.cellsgridjs.GridLoadFormat:
        '''Gets the load format by file extension
        
        :param extension: The file extention ,usually start with \'.\' .'''
        raise NotImplementedError()
    
    @staticmethod
    def get_image_url(uid : str, picid : str, delimiter : str) -> str:
        '''Gets the image URL.
        
        :param uid: The unique id for the file cache.
        :param picid: The image id.
        :param delimiter: The string delimiter.'''
        raise NotImplementedError()
    
    @staticmethod
    def set_image_url_base(base_image_url : str) -> None:
        '''Set the base image get action URL from controller .
        
        :param base_image_url: the base image get action URL.'''
        raise NotImplementedError()
    
    @property
    def settings(self) -> aspose.cellsgridjs.GridWorkbookSettings:
        '''Represents the workbook settings.'''
        raise NotImplementedError()
    
    @settings.setter
    def settings(self, value : aspose.cellsgridjs.GridWorkbookSettings) -> None:
        '''Represents the workbook settings.'''
        raise NotImplementedError()
    
    @staticmethod
    def set_cache_imp(value: aspose.cellsgridjs.GridCacheForStream) -> None:
        '''Custom  implemention for cache storage,If you want to store cache in stream way ,you  need to set and implement it.'''
    @property
    def cache_imp(self) -> aspose.cellsgridjs.GridCacheForStream:
        '''Custom  implemention for cache storage,If you want to store cache in stream way ,you  need to set and implement it.'''
        raise NotImplementedError()

    @staticmethod
    def set_calculate_engine(value: aspose.cellsgridjs.GridAbstractCalculationEngine) -> None:
        '''Custom  implemention for calculation engine ,If you want to do custom calculation, you  need to set and implement it.'''
    @property
    def calculate_engine(self) -> aspose.cellsgridjs.GridAbstractCalculationEngine:
        '''Custom  implemention for calculation engine ,If you want to do custom calculation, you  need to set and implement it.'''
        raise NotImplementedError()

    @staticmethod
    def set_update_monitor(value: aspose.cellsgridjs.GridUpdateMonitor) -> None:
        '''Gets/Sets the update monitor to track update operation'''
    @property
    def update_monitor(self) -> aspose.cellsgridjs.GridUpdateMonitor:
        '''Gets/Sets the update monitor to track update operation'''
        raise NotImplementedError()

    @property
    def PICTURE_TYPE(self) -> str:
        '''const value for the type of the image'''
        raise NotImplementedError()


class GridReferredArea:
    '''Represents a referred area by the formula.'''
    
    def get_values(self) -> Any:
        '''Gets cell values in this area.
        
        :returns: If this area is invalid, "#REF!" will be returned;
        If this area is one single cell, then return the cell value object;
        Otherwise return one array for all values in this area.'''
        raise NotImplementedError()
    
    def get_value(self, row_offset : int, col_offset : int) -> Any:
        '''Gets cell value with given offset from the top-left of this area.
        
        :param row_offset: row offset from the start row of this area
        :param col_offset: column offset from the start row of this area
        :returns: "#REF!" if this area is invalid;
        "#N/A" if given offset out of this area;
        Otherwise return the cell value at given position.'''
        raise NotImplementedError()
    
    @property
    def is_external_link(self) -> bool:
        '''Indicates whether this is an external link.'''
        raise NotImplementedError()
    
    @property
    def external_file_name(self) -> str:
        '''Get the external file name if this is an external reference.'''
        raise NotImplementedError()
    
    @property
    def sheet_name(self) -> str:
        '''Indicates which sheet this is in'''
        raise NotImplementedError()
    
    @property
    def is_area(self) -> bool:
        '''Indicates whether this is an area.'''
        raise NotImplementedError()
    
    @property
    def end_column(self) -> int:
        '''The end column of the area.'''
        raise NotImplementedError()
    
    @property
    def start_column(self) -> int:
        '''The start column of the area.'''
        raise NotImplementedError()
    
    @property
    def end_row(self) -> int:
        '''The end row of the area.'''
        raise NotImplementedError()
    
    @property
    def start_row(self) -> int:
        '''The start row of the area.'''
        raise NotImplementedError()
    

class GridUpdateMonitor:
    '''Monitor for user to track the change of update operation.'''
    
    def after_update(self, op : str, uid : str, cells : List[Any]) -> None:
        '''after update operation
        
        :param op: The JSON string for update operation
        :param uid: The unique id for the file cache.
        :param cells: The Updated Cells list,include cells which has style change,value change or formula change'''
        raise NotImplementedError()
    

class GridWorkbookSettings:
    '''Represents the settings of the workbook.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @property
    def max_iteration(self) -> int:
        '''Returns the maximum number of iterations to resolve a circular reference, the default value is 100.'''
        raise NotImplementedError()
    
    @max_iteration.setter
    def max_iteration(self, value : int) -> None:
        '''Returns or sets the maximum number of iterations to resolve a circular reference, the default value is 100.'''
        raise NotImplementedError()
    
    @property
    def iteration(self) -> bool:
        '''Indicates whether use iteration to resolve circular references.'''
        raise NotImplementedError()
    
    @iteration.setter
    def iteration(self, value : bool) -> None:
        '''Indicates whether use iteration to resolve circular references.'''
        raise NotImplementedError()
    
    @property
    def force_full_calculate(self) -> bool:
        '''Indicates whether fully calculates every time when a calculation is triggered.'''
        raise NotImplementedError()
    
    @force_full_calculate.setter
    def force_full_calculate(self, value : bool) -> None:
        '''Indicates whether fully calculates every time when a calculation is triggered.'''
        raise NotImplementedError()
    
    @property
    def create_calc_chain(self) -> bool:
        '''Indicates whether create calculated formulas chain. Default is false.'''
        raise NotImplementedError()
    
    @create_calc_chain.setter
    def create_calc_chain(self, value : bool) -> None:
        '''Indicates whether create calculated formulas chain. Default is false.'''
        raise NotImplementedError()
    
    @property
    def re_calculate_on_open(self) -> bool:
        '''Indicates whether re-calculate all formulas on opening file. Default is true.'''
        raise NotImplementedError()
    
    @re_calculate_on_open.setter
    def re_calculate_on_open(self, value : bool) -> None:
        '''Indicates whether re-calculate all formulas on opening file. Default is true.'''
        raise NotImplementedError()
    
    @property
    def precision_as_displayed(self) -> bool:
        '''True if calculations in this workbook will be done using only the precision of the numbers as they\'re displayed'''
        raise NotImplementedError()
    
    @precision_as_displayed.setter
    def precision_as_displayed(self, value : bool) -> None:
        '''True if calculations in this workbook will be done using only the precision of the numbers as they\'re displayed'''
        raise NotImplementedError()
    
    @property
    def date1904(self) -> bool:
        '''Gets a value which represents if the workbook uses the 1904 date system.'''
        raise NotImplementedError()
    
    @date1904.setter
    def date1904(self, value : bool) -> None:
        '''Sets a value which represents if the workbook uses the 1904 date system.'''
        raise NotImplementedError()
    
    @property
    def enable_macros(self) -> bool:
        '''Enable macros; Now it only works when copying a worksheet to other worksheet in a workbook.'''
        raise NotImplementedError()
    
    @enable_macros.setter
    def enable_macros(self, value : bool) -> None:
        '''Enable macros; Now it only works when copying a worksheet to other worksheet in a workbook.'''
        raise NotImplementedError()
    
    @property
    def check_custom_number_format(self) -> bool:
        '''Indicates whether checking custom number format when setting Style.Custom, default is false.'''
        raise NotImplementedError()
    
    @check_custom_number_format.setter
    def check_custom_number_format(self, value : bool) -> None:
        '''Indicates whether checking custom number format when setting Style.Custom, default is false.'''
        raise NotImplementedError()
    
    @property
    def check_excel_restriction(self) -> bool:
        '''Whether check restriction of excel file when user modify cells related objects.
        For example, excel does not allow inputting string value longer than 32K.
        When you input a value longer than 32K such as by Cell.PutValue(string), if this property is true, you will get an Exception.
        If this property is false, we will accept your input string value as the cell\'s value so that later
        you can output the complete string value for other file formats such as CSV.
        However, if you have set such kind of value that is invalid for excel file format,
        you should not save the workbook as excel file format later. Otherwise there may be unexpected error for the generated excel file.
        default is false.'''
        raise NotImplementedError()
    
    @check_excel_restriction.setter
    def check_excel_restriction(self, value : bool) -> None:
        '''Whether check restriction of excel file when user modify cells related objects.
        For example, excel does not allow inputting string value longer than 32K.
        When you input a value longer than 32K such as by Cell.PutValue(string), if this property is true, you will get an Exception.
        If this property is false, we will accept your input string value as the cell\'s value so that later
        you can output the complete string value for other file formats such as CSV.
        However, if you have set such kind of value that is invalid for excel file format,
        you should not save the workbook as excel file format later. Otherwise there may be unexpected error for the generated excel file.
        default is false.'''
        raise NotImplementedError()
    
    @property
    def author(self) -> str:
        '''Gets/sets the author of the file.'''
        raise NotImplementedError()
    
    @author.setter
    def author(self, value : str) -> None:
        '''Gets/sets the author of the file.'''
        raise NotImplementedError()
    

class IGridJsService:
    '''Reprensents the basic operation apis interface used in controller actions.'''
    
    def update_cell(self, p : str, uid : str) -> str:
        '''Applies the update operation.
        
        :param p: The JSON format string of update operation.
        :param uid: The unique id for the file cache.
        :returns: The JSON format string of the update result.'''
        raise NotImplementedError()
    
    def check_in_cache_for_collaborative(self, uid : str) -> bool:
        '''Check wether workbook instance is in memory cache .this method is apply for Collaborative mode only.'''
        raise NotImplementedError()
    
    def detail_stream_json_with_uid(self, stream : io._IOBase, file_path : str, uid : str) -> None:
        '''Write the JSON string  for the file to the stream  by the specified unique id.
        
        :param stream: The stream that will be written
        :param file_path: The file path
        :param uid: The unique id for the file cache.'''
        raise NotImplementedError()
    
    def detail_stream_json(self, stream : io._IOBase, file_path : str) -> None:
        '''Write the JSON string  for the Workbook to the stream
        
        :param stream: The stream that will be written
        :param file_path: The file path'''
        raise NotImplementedError()
    
    def lazy_loading_stream_json(self, stream : io._IOBase, sheet_name : str, uid : str) -> None:
        '''Writes the JSON string of the specified sheet in the file from the cache using the specified unique id  to the stream..
        
        :param stream: The stream that will be written
        :param sheet_name: The sheet name.
        :param uid: The unique id for the file cache.'''
        raise NotImplementedError()
    
    def add_image(self, p : str, uid : str, iscontrol : str, file_input_stream : io._IOBase) -> str:
        '''Applies the add image from local file operation.
        
        :param p: The JSON string parameter
        :param uid: The unique id for the file cache.
        :param iscontrol: Specify whether it is a control.
        :param file_input_stream: The input stream form file of the image
        :returns: The JSON string result'''
        raise NotImplementedError()
    
    def add_image_by_url(self, p : str, uid : str, imageurl : str) -> str:
        '''Applies the add image from remote URL operation.
        
        :param p: The JSON string parameter
        :param uid: The unique id for the file cache.
        :param imageurl: Specify the image URL.
        :returns: The JSON string result'''
        raise NotImplementedError()
    
    def copy_image(self, p : str, uid : str) -> str:
        '''Applies the copy image operation.
        
        :param p: The JSON string parameter
        :param uid: The unique id for the file cache.
        :returns: The JSON string result'''
        raise NotImplementedError()
    
    def load(self, uid : str, filename : str) -> str:
        '''Gets the JSON  string  of the file from the cache using the specified unique id,set the output filename in the JSON.
        
        :param uid: The unique id for the file cache.
        :param filename: Specifies the file name in the JSON. If set to null,the default filename is: book1.
        :returns: The JSON string'''
        raise NotImplementedError()
    
    def image(self, uid : str, picid : str) -> io._IOBase:
        '''Get Stream of image.
        
        :param uid: The unique id for the file cache.
        :param picid: The image id.
        :returns: The image stream'''
        raise NotImplementedError()
    
    def ole(self, uid : str, sheetname : str, oleid : int, label : List[str]) -> List[int]:
        '''Gets the byte array data of the  embedded ole object .
        
        :param uid: The unique id for the file cache.
        :param sheetname: The worksheet name.
        :param oleid: The  id for the embedded ole object.
        :param label: The display label of the embedded ole object.
        :returns: The byte array data of the  embedded ole object .'''
        raise NotImplementedError()
    
    def image_url(self, base_url : str, picid : str, uid : str) -> str:
        '''Gets the image URL.
        
        :param base_url: The base action URL.
        :param picid: The image id.
        :param uid: The unique id for the file cache.
        :returns: The image URL'''
        raise NotImplementedError()
    
    def get_file(self, fileid : str) -> io._IOBase:
        '''Get file stream
        
        :param fileid: the file id
        :returns: The stream of the file'''
        raise NotImplementedError()
    
    def download(self, p : str, uid : str, filename : str) -> str:
        '''Applies the download file operation
        
        :param p: The JSON parameter
        :param uid: The unique id for the file cache.
        :param filename: The file name
        :returns: The file URL'''
        raise NotImplementedError()
    

class ITextTranslator:
    '''Represents the interface for translate'''
    

class OprMessageService:
    '''This class provide all the operations for messages sync in Collaborative mode .'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    

class PdfSaveOptions:
    '''Represents the options for saving pdf file.'''
    
    def __init__(self) -> None:
        '''Creates the options for saving pdf file.'''
        raise NotImplementedError()
    
    @overload
    def set_sheet_set(self, sheet_indexes : List[int]) -> None:
        '''Creates a sheet set based on exact sheet indexes.
        
        :param sheet_indexes: zero based sheet indexes.'''
        raise NotImplementedError()
    
    @overload
    def set_sheet_set(self, sheet_names : List[str]) -> None:
        '''Creates a sheet set based on exact sheet names.
        
        :param sheet_names: sheet names.'''
        raise NotImplementedError()
    
    def set_image_resample(self, desired_ppi : int, jpeg_quality : int) -> None:
        '''Sets desired PPI(pixels per inch) of resample images and jpeg quality.
        All images will be converted to JPEG with the specified quality setting,
        and images that are greater than the specified PPI (pixels per inch) will be resampled.
        
        :param desired_ppi: Desired pixels per inch. 220 high quality. 150 screen quality. 96 email quality.
        :param jpeg_quality: 0 - 100% JPEG quality.'''
        raise NotImplementedError()
    
    @property
    def font_encoding(self) -> aspose.cellsgridjs.PdfFontEncoding:
        '''Gets embedded font encoding in pdf.'''
        raise NotImplementedError()
    
    @font_encoding.setter
    def font_encoding(self, value : aspose.cellsgridjs.PdfFontEncoding) -> None:
        '''Sets embedded font encoding in pdf.'''
        raise NotImplementedError()
    
    @property
    def display_doc_title(self) -> bool:
        '''Indicates whether the window\'s title bar should display the document title.'''
        raise NotImplementedError()
    
    @display_doc_title.setter
    def display_doc_title(self, value : bool) -> None:
        '''Indicates whether the window\'s title bar should display the document title.'''
        raise NotImplementedError()
    
    @property
    def export_document_structure(self) -> bool:
        '''Indicates whether to export document structure.'''
        raise NotImplementedError()
    
    @export_document_structure.setter
    def export_document_structure(self, value : bool) -> None:
        '''Indicates whether to export document structure.'''
        raise NotImplementedError()
    
    @property
    def custom_properties_export(self) -> aspose.cellsgridjs.PdfCustomPropertiesExport:
        '''Gets a value determining the way of custom document properties are exported to PDF file. Default value is None.'''
        raise NotImplementedError()
    
    @custom_properties_export.setter
    def custom_properties_export(self, value : aspose.cellsgridjs.PdfCustomPropertiesExport) -> None:
        '''Sets a value determining the way of custom document properties are exported to PDF file. Default value is None.'''
        raise NotImplementedError()
    
    @property
    def optimization_type(self) -> aspose.cellsgridjs.PdfOptimizationType:
        '''Gets and sets pdf optimization type.'''
        raise NotImplementedError()
    
    @optimization_type.setter
    def optimization_type(self, value : aspose.cellsgridjs.PdfOptimizationType) -> None:
        '''Gets and sets pdf optimization type.'''
        raise NotImplementedError()
    
    @property
    def producer(self) -> str:
        '''Gets and sets producer of generated pdf document.'''
        raise NotImplementedError()
    
    @producer.setter
    def producer(self, value : str) -> None:
        '''Gets and sets producer of generated pdf document.'''
        raise NotImplementedError()
    
    @property
    def created_time(self) -> datetime:
        '''Gets and sets the time of generating the pdf document.'''
        raise NotImplementedError()
    
    @created_time.setter
    def created_time(self, value : datetime) -> None:
        '''Gets and sets the time of generating the pdf document.'''
        raise NotImplementedError()
    
    @property
    def pdf_compression(self) -> aspose.cellsgridjs.PdfCompressionCore:
        '''Indicate the compression algorithm'''
        raise NotImplementedError()
    
    @pdf_compression.setter
    def pdf_compression(self, value : aspose.cellsgridjs.PdfCompressionCore) -> None:
        '''Indicate the compression algorithm'''
        raise NotImplementedError()
    
    @property
    def calculate_formula(self) -> bool:
        '''Indicates whether to calculate formulas before saving pdf file.'''
        raise NotImplementedError()
    
    @calculate_formula.setter
    def calculate_formula(self, value : bool) -> None:
        '''Indicates whether to calculate formulas before saving pdf file.'''
        raise NotImplementedError()
    
    @property
    def security_options(self) -> aspose.cellsgridjs.PdfSecurityOptions:
        '''Set this options, when security is need in xls2pdf result.'''
        raise NotImplementedError()
    
    @property
    def compliance(self) -> aspose.cellsgridjs.PdfCompliance:
        '''Gets the PDF standards compliance level for output documents.'''
        raise NotImplementedError()
    
    @compliance.setter
    def compliance(self, value : aspose.cellsgridjs.PdfCompliance) -> None:
        '''Sets the PDF standards compliance level for output documents.'''
        raise NotImplementedError()
    
    @property
    def embed_standard_windows_fonts(self) -> bool:
        '''True to embed true type fonts.
        Affects only ASCII characters 32-127.
        Fonts for character codes greater than 127 are always embedded.
        Fonts are always embedded for PDF/A-1a, PDF/A-1b standard.
        Default is true.'''
        raise NotImplementedError()
    
    @embed_standard_windows_fonts.setter
    def embed_standard_windows_fonts(self, value : bool) -> None:
        '''True to embed true type fonts.
        Affects only ASCII characters 32-127.
        Fonts for character codes greater than 127 are always embedded.
        Fonts are always embedded for PDF/A-1a, PDF/A-1b standard.
        Default is true.'''
        raise NotImplementedError()
    
    @property
    def embed_attachments(self) -> bool:
        '''Indicates whether to embed attachment for Ole objects in Excel.'''
        raise NotImplementedError()
    
    @embed_attachments.setter
    def embed_attachments(self, value : bool) -> None:
        '''Indicates whether to embed attachment for Ole objects in Excel.'''
        raise NotImplementedError()
    
    @property
    def default_edit_language(self) -> aspose.cellsgridjs.DefaultEditLanguage:
        '''Gets default edit language.'''
        raise NotImplementedError()
    
    @default_edit_language.setter
    def default_edit_language(self, value : aspose.cellsgridjs.DefaultEditLanguage) -> None:
        '''Sets default edit language.'''
        raise NotImplementedError()
    
    @property
    def text_cross_type(self) -> aspose.cellsgridjs.TextCrossType:
        '''Gets displaying text type when the text width is larger than cell width.'''
        raise NotImplementedError()
    
    @text_cross_type.setter
    def text_cross_type(self, value : aspose.cellsgridjs.TextCrossType) -> None:
        '''Sets displaying text type when the text width is larger than cell width.'''
        raise NotImplementedError()
    
    @property
    def gridline_color(self) -> aspose.pydrawing.Color:
        '''Gets gridline colr.'''
        raise NotImplementedError()
    
    @gridline_color.setter
    def gridline_color(self, value : aspose.pydrawing.Color) -> None:
        '''Sets gridline colr.'''
        raise NotImplementedError()
    
    @property
    def gridline_type(self) -> aspose.cellsgridjs.GridlineType:
        '''Gets gridline type.'''
        raise NotImplementedError()
    
    @gridline_type.setter
    def gridline_type(self, value : aspose.cellsgridjs.GridlineType) -> None:
        '''Sets gridline type.'''
        raise NotImplementedError()
    
    @property
    def printing_page_type(self) -> aspose.cellsgridjs.PrintingPageType:
        '''Indicates which pages will not be printed.'''
        raise NotImplementedError()
    
    @printing_page_type.setter
    def printing_page_type(self, value : aspose.cellsgridjs.PrintingPageType) -> None:
        '''Indicates which pages will not be printed.'''
        raise NotImplementedError()
    
    @property
    def emf_render_setting(self) -> aspose.cellsgridjs.EmfRenderSetting:
        '''Setting for rendering Emf metafile.'''
        raise NotImplementedError()
    
    @emf_render_setting.setter
    def emf_render_setting(self, value : aspose.cellsgridjs.EmfRenderSetting) -> None:
        '''Setting for rendering Emf metafile.'''
        raise NotImplementedError()
    
    @property
    def page_count(self) -> int:
        '''Gets the number of pages to save.'''
        raise NotImplementedError()
    
    @page_count.setter
    def page_count(self, value : int) -> None:
        '''Sets the number of pages to save.'''
        raise NotImplementedError()
    
    @property
    def page_index(self) -> int:
        '''Gets the 0-based index of the first page to save.'''
        raise NotImplementedError()
    
    @page_index.setter
    def page_index(self, value : int) -> None:
        '''Sets the 0-based index of the first page to save.'''
        raise NotImplementedError()
    
    @property
    def ignore_error(self) -> bool:
        '''Indicates if you need to hide the error while rendering.
        The error can be error in shape, image, chart rendering, etc.'''
        raise NotImplementedError()
    
    @ignore_error.setter
    def ignore_error(self, value : bool) -> None:
        '''Indicates if you need to hide the error while rendering.
        The error can be error in shape, image, chart rendering, etc.'''
        raise NotImplementedError()
    
    @property
    def output_blank_page_when_nothing_to_print(self) -> bool:
        '''Indicates whether to output a blank page when there is nothing to print.'''
        raise NotImplementedError()
    
    @output_blank_page_when_nothing_to_print.setter
    def output_blank_page_when_nothing_to_print(self, value : bool) -> None:
        '''Indicates whether to output a blank page when there is nothing to print.'''
        raise NotImplementedError()
    
    @property
    def default_font(self) -> str:
        '''When characters in the Excel are Unicode and not be set with correct font in cell style,
        They may appear as block in pdf,image.
        Set the DefaultFont such as MingLiu or MS Gothic to show these characters.
        If this property is not set, Aspose.Cells will use system default font to show these unicode characters.'''
        raise NotImplementedError()
    
    @default_font.setter
    def default_font(self, value : str) -> None:
        '''When characters in the Excel are Unicode and not be set with correct font in cell style,
        They may appear as block in pdf,image.
        Set the DefaultFont such as MingLiu or MS Gothic to show these characters.
        If this property is not set, Aspose.Cells will use system default font to show these unicode characters.'''
        raise NotImplementedError()
    
    @property
    def check_workbook_default_font(self) -> bool:
        '''When characters in the Excel are Unicode and not be set with correct font in cell style,
        They may appear as block in pdf,image.
        Set this to true to try to use workbook\'s default font to show these characters first.'''
        raise NotImplementedError()
    
    @check_workbook_default_font.setter
    def check_workbook_default_font(self, value : bool) -> None:
        '''When characters in the Excel are Unicode and not be set with correct font in cell style,
        They may appear as block in pdf,image.
        Set this to true to try to use workbook\'s default font to show these characters first.'''
        raise NotImplementedError()
    
    @property
    def check_font_compatibility(self) -> bool:
        '''Indicates whether to check font compatibility for every character in text.'''
        raise NotImplementedError()
    
    @check_font_compatibility.setter
    def check_font_compatibility(self, value : bool) -> None:
        '''Indicates whether to check font compatibility for every character in text.'''
        raise NotImplementedError()
    
    @property
    def is_font_substitution_char_granularity(self) -> bool:
        '''Indicates whether to only substitute the font of character when the cell font is not compatibility for it.'''
        raise NotImplementedError()
    
    @is_font_substitution_char_granularity.setter
    def is_font_substitution_char_granularity(self, value : bool) -> None:
        '''Indicates whether to only substitute the font of character when the cell font is not compatibility for it.'''
        raise NotImplementedError()
    
    @property
    def one_page_per_sheet(self) -> bool:
        '''If OnePagePerSheet is true , all content of one sheet will output to only one page in result.
        The paper size of pagesetup will be invalid, and the other settings of pagesetup
        will still take effect.'''
        raise NotImplementedError()
    
    @one_page_per_sheet.setter
    def one_page_per_sheet(self, value : bool) -> None:
        '''If OnePagePerSheet is true , all content of one sheet will output to only one page in result.
        The paper size of pagesetup will be invalid, and the other settings of pagesetup
        will still take effect.'''
        raise NotImplementedError()
    
    @property
    def all_columns_in_one_page_per_sheet(self) -> bool:
        '''If AllColumnsInOnePagePerSheet is true , all column content of one sheet will output to only one page in result.
        The width of paper size of pagesetup will be ignored, and the other settings of pagesetup
        will still take effect.'''
        raise NotImplementedError()
    
    @all_columns_in_one_page_per_sheet.setter
    def all_columns_in_one_page_per_sheet(self, value : bool) -> None:
        '''If AllColumnsInOnePagePerSheet is true , all column content of one sheet will output to only one page in result.
        The width of paper size of pagesetup will be ignored, and the other settings of pagesetup
        will still take effect.'''
        raise NotImplementedError()
    

class PdfSecurityOptions:
    '''Options for encrypting and access permissions for a PDF document.
    PDF/A does not allow security setting.'''
    
    def __init__(self) -> None:
        '''The constructor of PdfSecurityOptions'''
        raise NotImplementedError()
    
    @property
    def user_password(self) -> str:
        '''Gets the user password required for opening the encrypted PDF document.'''
        raise NotImplementedError()
    
    @user_password.setter
    def user_password(self, value : str) -> None:
        '''Sets the user password required for opening the encrypted PDF document.'''
        raise NotImplementedError()
    
    @property
    def owner_password(self) -> str:
        '''Gets the owner password for the encrypted PDF document.'''
        raise NotImplementedError()
    
    @owner_password.setter
    def owner_password(self, value : str) -> None:
        '''Sets the owner password for the encrypted PDF document.'''
        raise NotImplementedError()
    
    @property
    def print_permission(self) -> bool:
        '''Indicates whether to allow to print the document.'''
        raise NotImplementedError()
    
    @print_permission.setter
    def print_permission(self, value : bool) -> None:
        '''Indicates whether to allow to print the document.'''
        raise NotImplementedError()
    
    @property
    def modify_document_permission(self) -> bool:
        '''Indicates whether to allow to modify the contents of the document by operations other than those controlled
        by :py:attr:`aspose.cellsgridjs.PdfSecurityOptions.annotations_permission`, :py:attr:`aspose.cellsgridjs.PdfSecurityOptions.fill_forms_permission` and :py:attr:`aspose.cellsgridjs.PdfSecurityOptions.assemble_document_permission`.'''
        raise NotImplementedError()
    
    @modify_document_permission.setter
    def modify_document_permission(self, value : bool) -> None:
        '''Indicates whether to allow to modify the contents of the document by operations other than those controlled
        by :py:attr:`aspose.cellsgridjs.PdfSecurityOptions.annotations_permission`, :py:attr:`aspose.cellsgridjs.PdfSecurityOptions.fill_forms_permission` and :py:attr:`aspose.cellsgridjs.PdfSecurityOptions.assemble_document_permission`.'''
        raise NotImplementedError()
    
    @property
    def annotations_permission(self) -> bool:
        '''Indicates whether to allow to add or modify text annotations, fill in interactive form fields.'''
        raise NotImplementedError()
    
    @annotations_permission.setter
    def annotations_permission(self, value : bool) -> None:
        '''Indicates whether to allow to add or modify text annotations, fill in interactive form fields.'''
        raise NotImplementedError()
    
    @property
    def fill_forms_permission(self) -> bool:
        '''Indicates whether to allow to fill in existing interactive form fields (including signature fields),
        even if :py:attr:`aspose.cellsgridjs.PdfSecurityOptions.modify_document_permission` is clear.'''
        raise NotImplementedError()
    
    @fill_forms_permission.setter
    def fill_forms_permission(self, value : bool) -> None:
        '''Indicates whether to allow to fill in existing interactive form fields (including signature fields),
        even if :py:attr:`aspose.cellsgridjs.PdfSecurityOptions.modify_document_permission` is clear.'''
        raise NotImplementedError()
    
    @property
    def extract_content_permission(self) -> bool:
        '''Indicates whether to allow to copy or otherwise extract text and graphics from the document
        by operations other than that controlled by :py:attr:`aspose.cellsgridjs.PdfSecurityOptions.accessibility_extract_content`.'''
        raise NotImplementedError()
    
    @extract_content_permission.setter
    def extract_content_permission(self, value : bool) -> None:
        '''Indicates whether to allow to copy or otherwise extract text and graphics from the document
        by operations other than that controlled by :py:attr:`aspose.cellsgridjs.PdfSecurityOptions.accessibility_extract_content`.'''
        raise NotImplementedError()
    
    @property
    def accessibility_extract_content(self) -> bool:
        '''Indicates whether to allow to extract text and graphics (in support of accessibility to users with disabilities or for other purposes).'''
        raise NotImplementedError()
    
    @accessibility_extract_content.setter
    def accessibility_extract_content(self, value : bool) -> None:
        '''Indicates whether to allow to extract text and graphics (in support of accessibility to users with disabilities or for other purposes).'''
        raise NotImplementedError()
    
    @property
    def assemble_document_permission(self) -> bool:
        '''Indicates whether to allow to assemble the document (insert, rotate, or delete pages and create bookmarks or thumbnail images),
        even if :py:attr:`aspose.cellsgridjs.PdfSecurityOptions.modify_document_permission` is clear.'''
        raise NotImplementedError()
    
    @assemble_document_permission.setter
    def assemble_document_permission(self, value : bool) -> None:
        '''Indicates whether to allow to assemble the document (insert, rotate, or delete pages and create bookmarks or thumbnail images),
        even if :py:attr:`aspose.cellsgridjs.PdfSecurityOptions.modify_document_permission` is clear.'''
        raise NotImplementedError()
    
    @property
    def full_quality_print_permission(self) -> bool:
        '''Indicates whether to allow to print the document to a representation from
        which a faithful digital copy of the PDF content could be generated.'''
        raise NotImplementedError()
    
    @full_quality_print_permission.setter
    def full_quality_print_permission(self, value : bool) -> None:
        '''Indicates whether to allow to print the document to a representation from
        which a faithful digital copy of the PDF content could be generated.'''
        raise NotImplementedError()
    

class SheetSet:
    '''Describes a set of sheets.'''
    
    @overload
    def __init__(self, sheet_indexes : List[int]) -> None:
        '''Creates a sheet set based on exact sheet indexes.
        
        :param sheet_indexes: zero based sheet indexes.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, sheet_names : List[str]) -> None:
        '''Creates a sheet set based on exact sheet names.
        
        :param sheet_names: sheet names.'''
        raise NotImplementedError()
    

class CoWorkOperationType:
    '''Represents the action operation type in collabration mode.only available in java version now, will be available in .net/python version in future.'''
    
    VIEW : CoWorkOperationType
    '''View operation (read-only)'''
    LOAD : CoWorkOperationType
    '''Load operation (read-only)'''
    LOAD_SHEET : CoWorkOperationType
    '''Load sheet operation (read-only)'''
    GET_IMAGE : CoWorkOperationType
    '''Get image operation (read-only)'''
    GET_OLE : CoWorkOperationType
    '''Get OLE object operation (read-only)'''
    EDIT : CoWorkOperationType
    '''Edit operation (editable)'''
    UPDATE_CELL : CoWorkOperationType
    '''Update cell operation (editable)'''
    ADD_IMAGE : CoWorkOperationType
    '''Add image operation (editable)'''
    COPY_IMAGE : CoWorkOperationType
    '''Copy image operation (editable)'''
    INSERT_ROW : CoWorkOperationType
    '''Insert row operation (editable)'''
    DELETE_ROW : CoWorkOperationType
    '''Delete row operation (editable)'''
    INSERT_COLUMN : CoWorkOperationType
    '''Insert column operation (editable)'''
    DELETE_COLUMN : CoWorkOperationType
    '''Delete column operation (editable)'''
    DOWNLOAD : CoWorkOperationType
    '''Download operation'''
    ADMIN_CONFIG : CoWorkOperationType
    '''Admin configuration operation (administrative)'''
    USER_MANAGEMENT : CoWorkOperationType
    '''User management operation (administrative)'''

class CoWorkUserPermission:
    '''represent the user permission  in collaboration mode.only available in java version now, will be available in .net/python version in future.'''
    
    READ_ONLY : CoWorkUserPermission
    '''Read-only permission,User can only view the content but cannot make any modifications'''
    EDITABLE : CoWorkUserPermission
    '''Editable permission,User can view and edit the content'''
    DOWNLOAD : CoWorkUserPermission
    '''Download permission,User can view,edit and download the content to local storage'''
    ADMIN : CoWorkUserPermission
    '''Administrator permission,User has full access including management operations'''

class DefaultEditLanguage:
    '''Represents the default edit language.'''
    
    AUTO : DefaultEditLanguage
    '''Represents auto detecting edit language according to the text itself.'''
    ENGLISH : DefaultEditLanguage
    '''Represents English language.'''
    CJK : DefaultEditLanguage
    '''Represents Chinese, Japanese, Korean language.'''

class EmfRenderSetting:
    '''Setting for rendering Emf metafile.'''
    
    EMF_ONLY : EmfRenderSetting
    '''Only rendering Emf records.'''
    EMF_PLUS_PREFER : EmfRenderSetting
    '''Prefer rendering EmfPlus records.'''

class GridExceptionType:
    '''Represents custom exception code for GridJs.'''
    
    CHART : GridExceptionType
    '''Invalid chart setting.'''
    DATA_TYPE : GridExceptionType
    '''Invalid data type setting.'''
    DATA_VALIDATION : GridExceptionType
    '''Invalid data validation setting.'''
    CONDITIONAL_FORMATTING : GridExceptionType
    '''Invalid data validation setting.'''
    FILE_FORMAT : GridExceptionType
    '''Invalid file format.'''
    FORMULA : GridExceptionType
    '''Invalid formula.'''
    INVALID_DATA : GridExceptionType
    '''Invalid data.'''
    INVALID_OPERATOR : GridExceptionType
    '''Invalid operator.'''
    INCORRECT_PASSWORD : GridExceptionType
    '''Incorrect password.'''
    LICENSE : GridExceptionType
    '''License related errors.'''
    LIMITATION : GridExceptionType
    '''Out of MS Excel limitation error.'''
    PAGE_SETUP : GridExceptionType
    '''Invalid page setup setting.'''
    PIVOT_TABLE : GridExceptionType
    '''Invalid pivotTable setting.'''
    SHAPE : GridExceptionType
    '''Invalid drawing object setting.'''
    SPARKLINE : GridExceptionType
    '''Invalid sparkline object setting.'''
    SHEET_NAME : GridExceptionType
    '''Invalid worksheet name.'''
    SHEET_TYPE : GridExceptionType
    '''Invalid worksheet type.'''
    INTERRUPTED : GridExceptionType
    '''The process is interrupted.'''
    IO : GridExceptionType
    '''The file is invalid.'''
    PERMISSION : GridExceptionType
    '''Permission is required to open this file.'''
    UNSUPPORTED_FEATURE : GridExceptionType
    '''Unsupported feature.'''
    UNSUPPORTED_STREAM : GridExceptionType
    '''Unsupported stream to be opened.'''
    UNDISCLOSED_INFORMATION : GridExceptionType
    '''Files contains some undisclosed information.'''

class GridLoadFormat:
    '''Represents the load file format.'''
    
    AUTO : GridLoadFormat
    '''Represents recognizing the format automatically.'''
    CSV : GridLoadFormat
    '''Comma-Separated Values(CSV) text file.'''
    XLSX : GridLoadFormat
    '''Represents Office Open XML spreadsheetML workbook or template, with or without macros.'''
    TSV : GridLoadFormat
    '''Tab-Separated Values(TSV) text file.'''
    TAB_DELIMITED : GridLoadFormat
    '''Represents a tab delimited text file, same with :py:attr:`aspose.cellsgridjs.GridLoadFormat.TSV`.'''
    HTML : GridLoadFormat
    '''Represents a html file.'''
    M_HTML : GridLoadFormat
    '''Represents a mhtml file.'''
    ODS : GridLoadFormat
    '''Open Document Sheet(ODS) file.'''
    EXCEL_97_TO_2003 : GridLoadFormat
    '''Represents an Excel97-2003 xls file.'''
    SPREADSHEET_ML : GridLoadFormat
    '''Represents an Excel 2003 xml file.'''
    XLSB : GridLoadFormat
    '''Represents an xlsb file.'''
    OTS : GridLoadFormat
    '''Open Document Template Sheet(OTS) file.'''
    NUMBERS : GridLoadFormat
    '''Represents a numbers file.'''
    FODS : GridLoadFormat
    '''Represents OpenDocument Flat XML Spreadsheet (.fods) file format.'''
    SXC : GridLoadFormat
    '''Represents StarOffice Calc Spreadsheet (.sxc) file format.'''
    XML : GridLoadFormat
    '''Represents a simple xml file.'''
    EPUB : GridLoadFormat
    '''Reprents an EPUB file.'''
    AZW3 : GridLoadFormat
    '''Represents an AZW3 file.'''
    CHM : GridLoadFormat
    '''Represents a CHM file.'''
    MARKDOWN : GridLoadFormat
    '''Represents a Markdown file.'''
    UNKNOWN : GridLoadFormat
    '''Represents unrecognized format, cannot be loaded.'''
    IMAGE : GridLoadFormat
    '''Image'''
    JSON : GridLoadFormat
    '''Json'''
    DIF : GridLoadFormat
    '''Data Interchange Format.'''
    DBF : GridLoadFormat
    '''Xbase Data file'''

class GridlineType:
    '''Enumerates grid line Type.'''
    
    DOTTED : GridlineType
    '''Represents dotted line.'''
    HAIR : GridlineType
    '''Represents hair line.'''

class PdfCompliance:
    '''Allowing user to set PDF conversion\'s Compatibility'''
    
    PDF14 : PdfCompliance
    '''Pdf format compatible with PDF 1.4'''
    PDF15 : PdfCompliance
    '''Pdf format compatible with PDF 1.5'''
    PDF16 : PdfCompliance
    '''Pdf format compatible with PDF 1.6'''
    PDF17 : PdfCompliance
    '''Pdf format compatible with PDF 1.7'''
    PDF_A1B : PdfCompliance
    '''Pdf format compatible with PDF/A-1b(ISO 19005-1)'''
    PDF_A1A : PdfCompliance
    '''Pdf format compatible with PDF/A-1a(ISO 19005-1)'''
    PDF_A2B : PdfCompliance
    '''Pdf format compatible with PDF/A-2b(ISO 19005-2)'''
    PDF_A2U : PdfCompliance
    '''Pdf format compatible with PDF/A-2u(ISO 19005-2)'''
    PDF_A2A : PdfCompliance
    '''Pdf format compatible with PDF/A-2a(ISO 19005-2)'''
    PDF_A3B : PdfCompliance
    '''Pdf format compatible with PDF/A-3b(ISO 19005-3)'''
    PDF_A3U : PdfCompliance
    '''Pdf format compatible with PDF/A-3u(ISO 19005-3)'''
    PDF_A3A : PdfCompliance
    '''Pdf format compatible with PDF/A-3a(ISO 19005-3)'''

class PdfCompressionCore:
    '''Specifies a type of compression applied to all content in the PDF file except images.'''
    
    NONE : PdfCompressionCore
    '''None'''
    RLE : PdfCompressionCore
    '''Rle'''
    LZW : PdfCompressionCore
    '''Lzw'''
    FLATE : PdfCompressionCore
    '''Flate'''

class PdfCustomPropertiesExport:
    '''Specifies the way of custom document properties are exported to PDF file.'''
    
    NONE : PdfCustomPropertiesExport
    '''No custom properties are exported.'''
    STANDARD : PdfCustomPropertiesExport
    '''Custom properties are exported as entries in Info dictionary.'''

class PdfFontEncoding:
    '''Represents pdf embedded font encoding.'''
    
    IDENTITY : PdfFontEncoding
    '''Represents use Identity-H encoding for all embedded fonts in pdf.'''
    ANSI_PREFER : PdfFontEncoding
    '''Represents prefer to use WinAnsiEncoding for TrueType fonts with characters 32-127,
    otherwise, Identity-H encoding will be used for embedded fonts in pdf.'''

class PdfOptimizationType:
    '''Specifies a type of optimization.'''
    
    STANDARD : PdfOptimizationType
    '''High print quality'''
    MINIMUM_SIZE : PdfOptimizationType
    '''File size is more important than print quality'''

class PrintingPageType:
    '''Indicates which pages will not be printed.'''
    
    DEFAULT : PrintingPageType
    '''Prints all pages.'''
    IGNORE_BLANK : PrintingPageType
    '''Don\'t print the pages which the cells are blank.'''
    IGNORE_STYLE : PrintingPageType
    '''Don\'t print the pages which cells only contain styles.'''

class TextCrossType:
    '''Enumerates displaying text type when the text width is larger than cell width.'''
    
    DEFAULT : TextCrossType
    '''Display text like in Microsoft Excel.'''
    CROSS_KEEP : TextCrossType
    '''Display all the text by crossing other cells and keep text of crossed cells.'''
    CROSS_OVERRIDE : TextCrossType
    '''Display all the text by crossing other cells and override text of crossed cells.'''
    STRICT_IN_CELL : TextCrossType
    '''Only display the text within the width of cell.'''

