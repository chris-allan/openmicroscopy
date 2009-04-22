/*
 * ome.ij.dm.browser.TreeImageNode 
 *
 *------------------------------------------------------------------------------
 *  Copyright (C) 2006-2009 University of Dundee. All rights reserved.
 *
 *
 * 	This program is free software; you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation; either version 2 of the License, or
 *  (at your option) any later version.
 *  This program is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 *  
 *  You should have received a copy of the GNU General Public License along
 *  with this program; if not, write to the Free Software Foundation, Inc.,
 *  51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
 *
 *------------------------------------------------------------------------------
 */
package ome.ij.dm.browser;


//Java imports

//Third-party libraries

//Application-internal dependencies

/** 
 * 
 *
 * @author  Jean-Marie Burel &nbsp;&nbsp;&nbsp;&nbsp;
 * <a href="mailto:j.burel@dundee.ac.uk">j.burel@dundee.ac.uk</a>
 * @author Donald MacDonald &nbsp;&nbsp;&nbsp;&nbsp;
 * <a href="mailto:donald@lifesci.dundee.ac.uk">donald@lifesci.dundee.ac.uk</a>
 * @version 3.0
 * <small>
 * (<b>Internal version:</b> $Revision: $Date: $)
 * </small>
 * @since 3.0-Beta4
 */
public class TreeImageNode 
	extends TreeImageDisplay
{
    
	/**
     * Implemented as specified by superclass.
     * @see TreeImageDisplay#doAccept(TreeImageDisplayVisitor)
     */
    protected void doAccept(TreeImageDisplayVisitor visitor)
    {
        visitor.visit(this);
    }
    
    /**
     * Creates a new leaf node.
     * 
     * @param hierarchyObject The original object in the image hierarchy which
     *                        is visualized by this node. It has to be an image
     *                        object in this case. 
     *                        Never pass <code>null</code>.
     */
    public TreeImageNode(Object hierarchyObject)
    {
        super(hierarchyObject);
    }
    
    /**
     * Spits out a runtime exception because it's not possible to add a
     * child to a leaf node.
     * @see TreeImageDisplay#addChildDisplay(TreeImageDisplay)
     */
    public void addChildDisplay(TreeImageDisplay child)
    {
        throw new IllegalArgumentException(
                "Can't add a child to a TreeImageNode.");
    }
    
    /**
     * Always returns <code>false</code> as this is not a container node.
     * @see TreeImageDisplay#containsImages()
     */
    public boolean containsImages() { return false; }

    /**
     * Always returns <code>false</code> as this is not a container node.
     * @see TreeImageDisplay#isChildrenLoaded()
     */
    public boolean isChildrenLoaded() { return false; }

    /**
     * Spits out a runtime exception because it's not possible to add a
     * child to a leaf node.
     * @see TreeImageDisplay#setChildrenLoaded(Boolean)
     */
    public void setChildrenLoaded(Boolean childrenLoaded)
    {
        throw new IllegalArgumentException(
                "A TreeImageNode doesn't have children.");
    }
    
    /**
     * Makes a copy of the node.
     * @see TreeImageDisplay#copy()
     */
    public TreeImageDisplay copy()
    {
        TreeImageNode copy = new TreeImageNode(this.getUserObject());
        copy.setHighLight(this.getHighLight());
        copy.setToolTip(this.getToolTip());
        copy.setExpanded(this.isExpanded());
        return copy;
    }
    
}
