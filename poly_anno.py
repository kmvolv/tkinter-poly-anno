import customtkinter as ctk
from CTkMessagebox import CTkMessagebox
from PIL import Image, ImageTk
import tkinter as tk
import math
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon

ctk.set_appearance_mode("dark")
vertice_radius = 3                               # NOTE: To configure the radius of the dots used to indicate the vertices of the polygon
delete_overlap = True                            # NOTE: To configure whether to delete overlapping polygons
curr_vertice_color = "green"                     # NOTE: Color of the vertice that the polygon edge will be drawn from (Latest vertex)
set_vertice_color = "red"                        # NOTE: Color of the remaining vertices
line_color = "red"                               # NOTE: Color of the edge of the polygon

def check_intersection(line1, line2):
    """
    Check if two line segments intersect.
    
    Parameters:
        line1 (tuple): A tuple containing two points (x1, y1) and (x2, y2) that define the first line segment.
        line2 (tuple): A tuple containing two points (x3, y3) and (x4, y4) that define the second line segment.
    
    Returns:
    - bool: True if the line segments intersect, False otherwise.
    """
    x1, y1 = line1[0]
    x2, y2 = line1[1]
    
    x3, y3 = line2[0]
    x4, y4 = line2[1]

    def orientation(p, q, r):
        """
        Determines the orientation of three points.

        Parameters:
            p (tuple): The first point as a tuple (x, y).
            q (tuple): The second point as a tuple (x, y).
            r (tuple): The third point as a tuple (x, y).
        
        Returns:
            0 if the points are collinear, 1 if they are clockwise, 2 if they are counterclockwise.
        """
        val = (q[1] - p[1]) * (r[0] - q[0]) - (q[0] - p[0]) * (r[1] - q[1])
        if val == 0:
            return 0  # Collinear
        return 1 if val > 0 else 2  # Clockwise or counterclockwise

    def on_segment(p, q, r):
        """
        Check if a point q lies on the line segment defined by points p and r.

        Parameters:
            p (tuple): The coordinates of the first point (x, y).
            q (tuple): The coordinates of the point to check (x, y).
            r (tuple): The coordinates of the second point (x, y).

        Returns:
            bool: True if q lies on the line segment defined by p and r, False otherwise.
        """
        return (q[0] <= max(p[0], r[0]) and q[0] >= min(p[0], r[0]) and
                q[1] <= max(p[1], r[1]) and q[1] >= min(p[1], r[1]))

    o1 = orientation((x1, y1), (x2, y2), (x3, y3))
    o2 = orientation((x1, y1), (x2, y2), (x4, y4))
    o3 = orientation((x3, y3), (x4, y4), (x1, y1))
    o4 = orientation((x3, y3), (x4, y4), (x2, y2))

    if o1 != o2 and o3 != o4:
        return True  # Segments intersect

    if (o1 == 0 and on_segment((x1, y1), (x3, y3), (x2, y2))) or \
       (o2 == 0 and on_segment((x1, y1), (x4, y4), (x2, y2))) or \
       (o3 == 0 and on_segment((x3, y3), (x1, y1), (x4, y4))) or \
       (o4 == 0 and on_segment((x3, y3), (x2, y2), (x4, y4))):
        return True  # Segments are collinear and overlap

    return False  # Segments do not intersect
    

def check_poly_in(p1,p2,polygon):
    """
    Check if a point is inside a polygon using the Shapely library

    Parameters:
        p1: float or int - The x-coordinate of the point.
        p2: float or int - The y-coordinate of the point.
        polygon: Polygon - The polygon to check.

    Returns:
        bool - True if the point is inside the polygon, False otherwise.
    """
    point = Point(p1, p2)
    return (polygon.contains(point))
    
def main():
    root = ctk.CTk()
    root.title("Poly Annotation")

    global starting_vert
    starting_vert = None
    global poly_list
    poly_list = []
    global undo_list
    undo_list = []
    global curr_vertices_history
    curr_vertices_history = [[]]

    canvas = ctk.CTkCanvas(master=root, width = 728, height = 410, highlightthickness=0)
    canvas.pack()

    image = Image.open("./b.jpeg")
    photo = ImageTk.PhotoImage(image = image)

    canvas.create_image(0,0, image = photo, anchor = ctk.NW)

    def on_button_press(event):
        pass
        
    def undo_event():
        """
        Function to undo the last operation on the canvas
        
        """
        global undo_list, curr_vertices_history, starting_vert, poly_list
        
        try:
            canvas.delete(undo_list[-1][0])
        except:
            print("The point does not exist!")

        try:
            canvas.delete(undo_list[-1][1])
        except:
            print("This line does not exist!")

        if len(undo_list): 
            undo_list.pop()
        if len(undo_list) == 0:
            undo_btn.configure(state = ctk.DISABLED)
            curr_vertices_history = [[]]
            starting_vert = None
            return
    
        if undo_list[-1][0] is not None: canvas.itemconfig(undo_list[-1][0], fill=curr_vertice_color)

        if(curr_vertices_history[-1] == []):
            curr_vertices_history.pop()
            poly_list.pop()
            starting_vert = curr_vertices_history[-1][0]
        else: 
            curr_vertices_history[-1].pop()
            try:
                starting_vert = curr_vertices_history[-1][0]
            except:
                starting_vert = None

    def open_tag_popup(polygon):
        """
        Opens a new window through which the user enters the name of the tag attributed to the polygon

        """
        global poly_list

        canvas.bind("<ButtonPress-1>", lambda : None)
        canvas.bind("<ButtonRelease-1>", lambda : None)
        # root.withdraw()
        popup = ctk.CTkToplevel(root)
        popup.overrideredirect(True)

        popup.bind("<Button-1>", lambda event: event.widget.focus_set())
        popup.title("Polygon tag")
        popup.grab_set()

        tag_label = ctk.CTkLabel(popup, text="Name of polygon tag : ")
        tag_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")

        entry_new_part = ctk.CTkEntry(popup)
        
        entry_new_part.grid(row=0, column=1, padx=10, pady=5)

        def set_tag(*args):
            """
            Adds the part name as specified by user.

            """
            new_tag = entry_new_part.get()
            new_tag = new_tag.lower()
            if(new_tag == ""):
                CTkMessagebox(title="Error", message="The polygon tag cannot be empty!", icon="cancel")
                return
            else:
                filtered_polys = [item for item in poly_list if item[0] == new_tag]
                if len(filtered_polys):
                    CTkMessagebox(title="Error", message="Duplicate polygon tag detected! Please give a unique tag name.", icon = "cancel")
                    return
            poly_list.append((new_tag, polygon))
            popup.destroy()  
            canvas.bind("<ButtonPress-1>", on_button_press)
            canvas.bind("<ButtonRelease-1>", on_button_release) 
            # root.deiconify()   

        popup.bind("<Return>", set_tag)
        ok_button = ctk.CTkButton(popup, text="OK")
        ok_button.bind("<ButtonRelease-1>", set_tag)
        ok_button.grid(row=2, column=0, columnspan=2, pady=10)


    def on_button_release(event):
        """
        Handles the button release event.

        This function checks if the released button overlaps with any existing dots or polygons.
        If it overlaps with a dot, it checks if it is the starting dot for a polygon. If it is, it completes the polygon.
        If it overlaps with a polygon, it does not draw the dot.
        It also checks if the connecting line between the previous dot and the released dot intersects with any existing lines.
        If it does, it does not draw the line.
        If none of the above conditions are met, it draws the dot and the connecting line.

        Parameters:
        - event: The event object representing the button release.

        """
        global starting_vert, poly_list, undo_list, curr_vertices_history

        make_polygon = False

        for polygon in curr_vertices_history:
            for vertice in polygon:
                dist = math.dist((event.x, event.y), vertice["center"])
                if (dist < 2*vertice_radius):
                    if(vertice == starting_vert):
                        make_polygon = True
                        break
                    else:
                        print("Dot overlap!")
                        return

        # Checking overlap with other polygons
        for polygon in poly_list:
            if(check_poly_in(event.x, event.y, polygon[1])):
                print("This point is inside a polygon!! Not gonna draw this ponit")
                return

        # Drawing connecting line, if exists
        try:
            prev_point = curr_vertices_history[-1][-1]
        except:
            print("This is the first point")
        else:
            # Now I need to check if it intersects with any other line :
            newline = [curr_vertices_history[-1][-1]["center"], (event.x, event.y)]
            for polygon in curr_vertices_history:
                for i in range(1,len(polygon)):
                    line1 = [polygon[i-1]["center"], polygon[i]["center"]]

                    if(line1[-1] != newline[0] and check_intersection(line1,newline)):
                        print('There are intersecting lines! Not gonna draw  >: (')
                        return
    
            if len(undo_list):
                canvas.itemconfig(undo_list[-1][0], fill=set_vertice_color)
            
            if not make_polygon:
                myline = canvas.create_line(prev_point["center"], (event.x, event.y), fill=line_color, width=2)
                undo_list.append([None, myline])
                undo_btn.configure(state = ctk.NORMAL)
            elif len(curr_vertices_history[-1])<2:
                print("You're drawing a polygon that cannot exist buddy")
                return
            else:
                print("Completing polygon okay?")
                myline = canvas.create_line(prev_point["center"], starting_vert["center"], fill=line_color, width=2)
                undo_list.append([None, myline])
                undo_btn.configure(state = ctk.NORMAL)
            
                vert_sequence = []
                for vertice in curr_vertices_history[-1]:
                    vert_sequence.append(vertice['center'])

                # This is to check if the polygon contains another polygon
                if delete_overlap:
                    poly_list.append((None, Polygon(vert_sequence)))
                    for idx in range(len(poly_list)-1):
                        if(poly_list[-1][1].contains(poly_list[idx][1])):
                            print("There are overlapping polygons!! I will delete this polygon!")
                            num_points = len(curr_vertices_history[-1]) + 1
                            while(num_points):
                                num_points-=1
                                undo_event()
                            starting_vert = None
                            curr_vertices_history.append([])
                            return
                    poly_list.pop()
                
                open_tag_popup(Polygon(vert_sequence))

                starting_vert = None
                curr_vertices_history.append([])
                return

        
        x1, y1 = (event.x - vertice_radius), (event.y - vertice_radius)
        x2, y2 = (event.x + vertice_radius), (event.y + vertice_radius)

        new_vertice = {"xy1": (x1,y1), "xy2": (x2,y2), "center": (event.x,event.y)}

        if(len(curr_vertices_history[-1]) == 0):
            undo_list.append([None,None])
            starting_vert = new_vertice

        curr_vertices_history[-1].append(new_vertice)

        undo_list[-1][0] = canvas.create_oval(x1,y1,x2,y2, fill=curr_vertice_color)
        undo_btn.configure(state = ctk.NORMAL)
        

        # oval_list.append(canvas.create_oval(x1,y1,x2,y2, fill="#FF0000"))
        print("This is poly list : ", poly_list)


    canvas.bind("<ButtonPress-1>", on_button_press)
    canvas.bind("<ButtonRelease-1>", on_button_release)

    undo_btn = ctk.CTkButton(master = root, text="Undo", command = undo_event, anchor=tk.CENTER, state=ctk.DISABLED)
    undo_btn.pack(padx=10, pady=5)

    root.mainloop()

if __name__ == '__main__':
    main()